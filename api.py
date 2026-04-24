import json
import urllib.request
from pathlib import Path
import webview
from chroma_manager import ChromaManager
from logger import get_logger

log = get_logger("api")

# 集合级 embedding 配置：{conn_id:collection_name -> {url, model, api_key}}
EMBED_CFG_PATH = Path.home() / ".chroma_walnut_ui" / "collection_embeddings.json"


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
        return cfg

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
        log.info("Embedding config saved: conn=%s collection=%s model=%s", conn_id, collection, embedding_model)
        return {"success": True}

    def clear_collection_embedding(self, conn_id: str, collection: str) -> dict:
        data = _load_embed_cfg()
        data.pop(_embed_key(conn_id, collection), None)
        _save_embed_cfg(data)
        log.info("Embedding config cleared: conn=%s collection=%s", conn_id, collection)
        return {"success": True}

    def test_embedding(self, conn_id: str, collection: str, text: str) -> dict:
        try:
            emb = self._call_embedding(conn_id, collection, text)
            if not emb:
                return {"error": "未配置嵌入模型"}
            return {"dimension": len(emb), "preview": [round(v, 6) for v in emb[:5]]}
        except Exception as e:
            log.error("test_embedding failed: conn=%s collection=%s error=%s", conn_id, collection, e)
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
        result = self._mgr.add_connection(name, conn_type, host, int(port), is_local, path, token)
        log.info("Connection added: name=%s type=%s", name, conn_type)
        return result

    def update_connection(self, conn_id: str, name: str, conn_type: str, host: str, port: int, is_local: bool, path: str, token: str = "") -> dict:
        result = self._mgr.update_connection(conn_id, name, conn_type, host, int(port), is_local, path, token)
        log.info("Connection updated: conn=%s name=%s", conn_id, name)
        return result

    def remove_connection(self, conn_id: str) -> bool:
        result = self._mgr.remove_connection(conn_id)
        log.info("Connection removed: conn=%s", conn_id)
        return result

    def test_connection(self, conn_type: str, host: str, port: int, path: str, token: str = "") -> dict:
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
            log.info("Connection test OK: type=%s host=%s port=%s", conn_type, host, port)
            return {"success": True}
        except Exception as e:
            log.warning("Connection test failed: type=%s host=%s port=%s error=%s", conn_type, host, port, e)
            return {"success": False, "error": str(e)}

    def connect(self, conn_id: str) -> dict:
        result = self._mgr.connect(conn_id)
        if result.get("success"):
            log.info("Connected: conn=%s", conn_id)
        else:
            log.warning("Connect failed: conn=%s error=%s", conn_id, result.get("error"))
        return result

    def disconnect(self, conn_id: str) -> bool:
        self._mgr.disconnect(conn_id)
        log.info("Disconnected: conn=%s", conn_id)
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
            log.error("list_collections failed: conn=%s error=%s", conn_id, e)
            return {"error": str(e)}

    def create_collection(self, conn_id: str, name: str, metadata_json: str = '') -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            metadata = json.loads(metadata_json) if metadata_json else None
            col = client.create_collection(name=name, metadata=metadata)
            log.info("Collection created: conn=%s name=%s", conn_id, name)
            return {"success": True, "name": col.name}
        except Exception as e:
            log.error("create_collection failed: conn=%s name=%s error=%s", conn_id, name, e)
            return {"success": False, "error": str(e)}

    def modify_collection(self, conn_id: str, old_name: str, new_name: str, metadata_json: str = '') -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            col = client.get_collection(name=old_name)
            metadata = json.loads(metadata_json) if metadata_json else None
            col.modify(name=new_name, metadata=metadata)
            if old_name != new_name:
                data = _load_embed_cfg()
                old_key = _embed_key(conn_id, old_name)
                new_key = _embed_key(conn_id, new_name)
                if old_key in data:
                    data[new_key] = data.pop(old_key)
                    _save_embed_cfg(data)
            log.info("Collection modified: conn=%s %s -> %s", conn_id, old_name, new_name)
            return {"success": True, "name": new_name}
        except Exception as e:
            log.error("modify_collection failed: conn=%s name=%s error=%s", conn_id, old_name, e)
            return {"success": False, "error": str(e)}

    def delete_collection(self, conn_id: str, name: str) -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            client.delete_collection(name=name)
            data = _load_embed_cfg()
            data.pop(_embed_key(conn_id, name), None)
            _save_embed_cfg(data)
            log.info("Collection deleted: conn=%s name=%s", conn_id, name)
            return {"success": True}
        except Exception as e:
            log.error("delete_collection failed: conn=%s name=%s error=%s", conn_id, name, e)
            return {"success": False, "error": str(e)}

    def get_collection_info(self, conn_id: str, name: str) -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            col = client.get_collection(name=name)
            return {"name": col.name, "count": col.count(), "metadata": col.metadata or {}}
        except Exception as e:
            log.error("get_collection_info failed: conn=%s name=%s error=%s", conn_id, name, e)
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
            log.error("get_documents failed: conn=%s collection=%s error=%s", conn_id, collection, e)
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
            log.info("Document added: conn=%s collection=%s id=%s", conn_id, collection, doc_id)
            return {"success": True}
        except Exception as e:
            log.error("add_document failed: conn=%s collection=%s id=%s error=%s", conn_id, collection, doc_id, e)
            return {"success": False, "error": str(e)}

    def seed_test_data(self, conn_id: str, collection: str) -> dict:
        _SEED_DOCS = [
            ("人工智能正在改变我们的生活方式，从智能家居到自动驾驶，无处不在。", "tech", 1),
            ("深度学习是机器学习的一个子领域，通过多层神经网络来学习数据的表示。", "tech", 2),
            ("自然语言处理让计算机能够理解和生成人类语言，是AI的重要分支。", "tech", 3),
            ("向量数据库专门用于存储和检索高维向量数据，是RAG系统的核心组件。", "tech", 4),
            ("大语言模型通过海量文本数据训练，能够执行各种语言理解和生成任务。", "tech", 5),
            ("Python是数据科学和机器学习领域最流行的编程语言之一。", "tech", 6),
            ("云计算的兴起让企业可以按需使用计算资源，大大降低了IT成本。", "tech", 7),
            ("区块链技术通过去中心化的方式保证数据的不可篡改性和透明性。", "tech", 8),
            ("量子计算利用量子力学原理，有望在特定问题上超越传统计算机。", "tech", 9),
            ("边缘计算将数据处理移至靠近数据源的位置，降低延迟并减轻云端压力。", "tech", 10),
            ("气候变化是当今世界面临的最严峻挑战之一，需要全球共同应对。", "science", 11),
            ("太阳能和风能等可再生能源正在快速替代传统化石燃料。", "science", 12),
            ("CRISPR基因编辑技术为治疗遗传性疾病带来了革命性的可能性。", "science", 13),
            ("黑洞是宇宙中密度极大的天体，连光也无法逃脱其引力。", "science", 14),
            ("疫苗的发明是人类医学史上最重要的成就之一，拯救了数十亿人的生命。", "science", 15),
            ("纳米技术在医疗、材料和电子领域展现出巨大的应用潜力。", "science", 16),
            ("海洋占地球表面积的71%，但人类对深海的探索仍然十分有限。", "science", 17),
            ("脑机接口技术正在帮助瘫痪患者重新获得与外界沟通的能力。", "science", 18),
            ("干细胞研究为再生医学开辟了新的道路，有望修复受损器官。", "science", 19),
            ("天文学家发现越来越多的系外行星，其中一些可能适合生命存在。", "science", 20),
            ("唐朝是中国历史上最繁荣的时期之一，文化艺术达到了新的高峰。", "history", 21),
            ("丝绸之路连接了东西方文明，促进了贸易、文化和知识的交流。", "history", 22),
            ("工业革命从英国开始，彻底改变了人类的生产方式和社会结构。", "history", 23),
            ("古罗马帝国的法律体系对现代西方法律产生了深远的影响。", "history", 24),
            ("郑和下西洋是人类历史上规模最大的航海探险活动之一。", "history", 25),
            ("文艺复兴运动重新发现了古典文化，推动了科学和艺术的蓬勃发展。", "history", 26),
            ("第二次世界大战是人类历史上最具破坏性的武装冲突，深刻改变了世界格局。", "history", 27),
            ("古埃及文明以其宏伟的金字塔和精密的天文历法而闻名于世。", "history", 28),
            ("印刷术的发明极大地推动了知识的传播和文艺复兴的到来。", "history", 29),
            ("冷战期间，美苏两国的太空竞赛推动了人类航天技术的飞速发展。", "history", 30),
            ("冥想和正念练习有助于减轻压力、改善注意力和提升整体幸福感。", "lifestyle", 31),
            ("均衡饮食和规律运动是维持健康生活方式的两大基石。", "lifestyle", 32),
            ("阅读不仅能增长知识，还能提升同理心和创造性思维能力。", "lifestyle", 33),
            ("良好的睡眠习惯对身体健康和认知功能至关重要。", "lifestyle", 34),
            ("旅行能拓宽视野，让人更好地理解不同文化和生活方式。", "lifestyle", 35),
            ("园艺不仅是一种休闲活动，还有助于减轻焦虑和改善心理健康。", "lifestyle", 36),
            ("学习一门新语言可以延缓认知退化并增强大脑的可塑性。", "lifestyle", 37),
            ("志愿服务能增强社区凝聚力，同时也给志愿者带来满足感和幸福感。", "lifestyle", 38),
            ("数字排毒帮助人们减少对屏幕的依赖，找回现实生活中的专注力。", "lifestyle", 39),
            ("烹饪自己的食物不仅更健康，也是一种创造性的自我表达方式。", "lifestyle", 40),
            ("全球化使各国经济深度融合，既带来机遇也带来新的挑战。", "economy", 41),
            ("数字货币的兴起正在重塑传统金融体系和支付方式。", "economy", 42),
            ("电商的普及彻底改变了零售业的商业模式和消费者行为。", "economy", 43),
            ("碳排放交易市场是通过市场机制应对气候变化的重要手段。", "economy", 44),
            ("人口老龄化是许多发达国家面临的共同挑战，影响社会保障和劳动力市场。", "economy", 45),
            ("共享经济模式通过平台连接闲置资源与需求方，提高了资源利用效率。", "economy", 46),
            ("供应链管理的优化对于提升企业竞争力和应对全球风险至关重要。", "economy", 47),
            ("绿色经济倡导在经济发展的同时保护环境，实现可持续增长。", "economy", 48),
            ("创业生态系统的繁荣需要资本、人才、政策和文化的共同支撑。", "economy", 49),
            ("数据已成为21世纪最重要的生产要素，驱动着新经济的发展。", "economy", 50),
        ]
        try:
            import uuid
            client = self._mgr.get_client(conn_id)
            col = client.get_collection(name=collection)
            ids, documents, metadatas, embeddings = [], [], [], []
            for text, category, idx in _SEED_DOCS:
                doc_id = f"seed-{uuid.uuid4().hex[:8]}"
                emb = self._call_embedding(conn_id, collection, text)
                ids.append(doc_id)
                documents.append(text)
                metadatas.append({"category": category, "index": idx})
                if emb:
                    embeddings.append(emb)
            kwargs: dict = {"ids": ids, "documents": documents, "metadatas": metadatas}
            if len(embeddings) == len(ids):
                kwargs["embeddings"] = embeddings
            col.add(**kwargs)
            log.info("Seed data added: conn=%s collection=%s count=%d", conn_id, collection, len(ids))
            return {"success": True, "count": len(ids)}
        except Exception as e:
            log.error("seed_test_data failed: conn=%s collection=%s error=%s", conn_id, collection, e)
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
            log.info("Document updated: conn=%s collection=%s id=%s", conn_id, collection, doc_id)
            return {"success": True}
        except Exception as e:
            log.error("update_document failed: conn=%s collection=%s id=%s error=%s", conn_id, collection, doc_id, e)
            return {"success": False, "error": str(e)}

    def delete_document(self, conn_id: str, collection: str, doc_id: str) -> dict:
        try:
            client = self._mgr.get_client(conn_id)
            col = client.get_collection(name=collection)
            col.delete(ids=[doc_id])
            log.info("Document deleted: conn=%s collection=%s id=%s", conn_id, collection, doc_id)
            return {"success": True}
        except Exception as e:
            log.error("delete_document failed: conn=%s collection=%s id=%s error=%s", conn_id, collection, doc_id, e)
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
            log.error("get_embedding_info failed: conn=%s collection=%s error=%s", conn_id, collection, e)
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
            log.info("Query executed: conn=%s collection=%s n_results=%s", conn_id, collection, n_results)
            return {"items": items}
        except Exception as e:
            log.error("query failed: conn=%s collection=%s error=%s", conn_id, collection, e)
            return {"error": str(e)}
