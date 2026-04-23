import json
import urllib.request
from pathlib import Path
import webview
from chroma_manager import ChromaManager

# 集合级 embedding 配置：{conn_id:collection_name -> {url, model, api_key}}
EMBED_CFG_PATH = Path.home() / ".chroma_ui" / "collection_embeddings.json"


def _load_embed_cfg() -> dict:
    if EMBED_CFG_PATH.exists():
        return json.loads(EMBED_CFG_PATH.read_text(encoding="utf-8"))
    return {}


def _save_embed_cfg(data: dict):
    EMBED_CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    EMBED_CFG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _embed_key(conn_id: str, collection: str) -> str:
    return f"{conn_id}:{collection}"


class API:
    def __init__(self):
        self._mgr = ChromaManager()

    # ── 集合级 embedding 配置 ─────────────────────────────────────────────────

    def get_collection_embedding(self, conn_id: str, collection: str) -> dict:
        cfg = _load_embed_cfg().get(_embed_key(conn_id, collection), {})
        return cfg  # {"embedding_url": ..., "embedding_model": ..., "embedding_api_key": ...} or {}

    def set_collection_embedding(self, conn_id: str, collection: str,
                                  embedding_url: str, embedding_model: str,
                                  embedding_api_key: str, dimension: int = 0) -> dict:
        data = _load_embed_cfg()
        data[_embed_key(conn_id, collection)] = {
            "embedding_url": embedding_url,
            "embedding_model": embedding_model,
            "embedding_api_key": embedding_api_key,
            "dimension": dimension or 0,
        }
        _save_embed_cfg(data)
        return {"success": True}

    def clear_collection_embedding(self, conn_id: str, collection: str) -> dict:
        data = _load_embed_cfg()
        data.pop(_embed_key(conn_id, collection), None)
        _save_embed_cfg(data)
        return {"success": True}

    def test_embedding(self, conn_id: str, collection: str, text: str) -> dict:
        try:
            emb = self._call_embedding(conn_id, collection, text)
            if not emb:
                return {"error": "未配置嵌入模型"}
            return {"dimension": len(emb), "preview": [round(v, 6) for v in emb[:5]]}
        except Exception as e:
            return {"error": str(e)}

    def _call_embedding(self, conn_id: str, collection: str, text: str) -> list:
        cfg = _load_embed_cfg().get(_embed_key(conn_id, collection), {})
        url = cfg.get("embedding_url", "")
        model = cfg.get("embedding_model", "")
        api_key = cfg.get("embedding_api_key", "")
        if not url or not model:
            return []
        payload = json.dumps({"model": model, "input": text}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data["data"][0]["embedding"]

    # ── 连接管理 ──────────────────────────────────────────────────────────────

    def get_connections(self) -> list:
        return self._mgr.list_connections()

    def add_connection(self, name: str, conn_type: str, host: str, port: int, is_local: bool, path: str, token: str = "") -> dict:
        return self._mgr.add_connection(name, conn_type, host, int(port), is_local, path, token)

    def update_connection(self, conn_id: str, name: str, conn_type: str, host: str, port: int, is_local: bool, path: str, token: str = "") -> dict:
        return self._mgr.update_connection(conn_id, name, conn_type, host, int(port), is_local, path, token)

    def remove_connection(self, conn_id: str) -> bool:
        return self._mgr.remove_connection(conn_id)

    def test_connection(self, conn_type: str, host: str, port: int, path: str, token: str = "") -> dict:
        """临时测试连接，不保存，不影响现有连接状态。"""
        import chromadb
        try:
            if conn_type == "persistent":
                if not path:
                    return {"success": False, "error": "未指定本地目录路径"}
                client = chromadb.PersistentClient(path=path)
            else:
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                client = chromadb.HttpClient(host=host, port=int(port), headers=headers)
                client.heartbeat()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def connect(self, conn_id: str) -> dict:
        return self._mgr.connect(conn_id)

    def disconnect(self, conn_id: str) -> bool:
        self._mgr.disconnect(conn_id)
        return True

    def pick_directory(self) -> str | None:
        windows = webview.windows
        if not windows:
            return None
        result = windows[0].create_file_dialog(webview.FileDialog.FOLDER)
        if result and len(result) > 0:
            return result[0]
        return None

    # ── 集合 ──────────────────────────────────────────────────────────────────

    def list_collections(self, conn_id: str) -> list:
        try:
            client = self._mgr.get_client(conn_id)
            cols = client.list_collections()
            embed_cfg = _load_embed_cfg()
            result = []
            for col in cols:
                key = _embed_key(conn_id, col.name)
                result.append({
                    "name": col.name,
                    "count": col.count(),
                    "metadata": col.metadata or {},
                    "has_embedding": bool(embed_cfg.get(key, {}).get("embedding_model")),
                })
            return result
        except Exception as e:
            return {"error": str(e)}

    def create_collection(self, conn_id: str, name: str) -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            col = client.create_collection(name=name)
            return {"success": True, "name": col.name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_collection(self, conn_id: str, name: str) -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            client.delete_collection(name=name)
            # 同时清除 embedding 配置
            data = _load_embed_cfg()
            data.pop(_embed_key(conn_id, name), None)
            _save_embed_cfg(data)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_collection_info(self, conn_id: str, name: str) -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            col = client.get_collection(name=name)
            return {"name": col.name, "count": col.count(), "metadata": col.metadata or {}}
        except Exception as e:
            return {"error": str(e)}

    # ── 文档 ──────────────────────────────────────────────────────────────────

    def get_documents(self, conn_id: str, collection: str, limit: int = 20, offset: int = 0, include_embeddings: bool = False) -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            col = client.get_collection(name=collection)
            total = col.count()
            includes = ["documents", "metadatas"]
            if include_embeddings:
                includes.append("embeddings")
            result = col.get(limit=int(limit), offset=int(offset), include=includes)
            embeddings = result.get("embeddings")
            items = []
            for i, doc_id in enumerate(result["ids"]):
                emb = None
                if embeddings is not None and i < len(embeddings) and embeddings[i] is not None:
                    emb = [round(float(v), 6) for v in embeddings[i]]
                raw_meta = result["metadatas"][i] if result["metadatas"] else None
                items.append({
                    "id": doc_id,
                    "document": result["documents"][i] if result["documents"] else "",
                    "metadata": raw_meta or {},
                    "embedding": emb,
                })
            return {"total": total, "items": items}
        except Exception as e:
            return {"error": str(e)}

    def add_document(self, conn_id: str, collection: str, doc_id: str, document: str, metadata_json: str) -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            col = client.get_collection(name=collection)
            metadata = json.loads(metadata_json) if metadata_json else {}
            kwargs: dict = {"ids": [doc_id], "documents": [document]}
            if metadata:
                kwargs["metadatas"] = [metadata]
            emb = self._call_embedding(conn_id, collection, document)
            if emb:
                kwargs["embeddings"] = [emb]
            col.add(**kwargs)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_document(self, conn_id: str, collection: str, doc_id: str, document: str, metadata_json: str) -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            col = client.get_collection(name=collection)
            metadata = json.loads(metadata_json) if metadata_json else {}
            kwargs: dict = {"ids": [doc_id], "documents": [document]}
            if metadata:
                kwargs["metadatas"] = [metadata]
            emb = self._call_embedding(conn_id, collection, document)
            if emb:
                kwargs["embeddings"] = [emb]
            col.update(**kwargs)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_document(self, conn_id: str, collection: str, doc_id: str) -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            col = client.get_collection(name=collection)
            col.delete(ids=[doc_id])
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── 向量信息 ──────────────────────────────────────────────────────────────

    def get_embedding_info(self, conn_id: str, collection: str) -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            col = client.get_collection(name=collection)
            result = col.get(limit=1, include=["embeddings"])
            embeddings = result.get("embeddings")
            if embeddings is None or len(embeddings) == 0:
                return {"dimension": None}
            first = embeddings[0]
            if first is None:
                return {"dimension": None}
            return {"dimension": int(len(first))}
        except Exception as e:
            return {"error": str(e), "dimension": None}

    # ── 查询 ──────────────────────────────────────────────────────────────────

    def query(self, conn_id: str, collection: str, query_text: str, n_results: int, where_json: str) -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            col = client.get_collection(name=collection)
            kwargs: dict = {
                "n_results": int(n_results),
                "include": ["documents", "metadatas", "distances"],
            }
            emb = self._call_embedding(conn_id, collection, query_text)
            if emb:
                kwargs["query_embeddings"] = [emb]
            else:
                kwargs["query_texts"] = [query_text]
            if where_json:
                kwargs["where"] = json.loads(where_json)
            result = col.query(**kwargs)
            items = []
            ids = result["ids"][0]
            docs = result["documents"][0] if result["documents"] else []
            metas = result["metadatas"][0] if result["metadatas"] else []
            dists = result["distances"][0] if result["distances"] else []
            for i, doc_id in enumerate(ids):
                raw_meta = metas[i] if i < len(metas) else None
                items.append({
                    "id": doc_id,
                    "document": docs[i] if i < len(docs) else "",
                    "metadata": raw_meta or {},
                    "distance": dists[i] if i < len(dists) else None,
                })
            return {"items": items}
        except Exception as e:
            return {"error": str(e)}
