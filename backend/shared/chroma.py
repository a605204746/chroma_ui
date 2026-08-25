"""ChromaDB 多连接管理器 — 所有 feature bridge 共享的 Chroma 客户端池。"""
import asyncio
import functools
import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Union

import chromadb


@dataclass
class ConnectionConfig:
    id: str
    name: str
    conn_type: str          # 'http' | 'persistent'
    host: str = ""
    port: int = 8000
    is_local: bool = True
    path: str = ""          # persist_directory，仅 persistent 类型使用
    token: str = ""         # Bearer token，仅 http 类型使用

    def to_dict(self):
        return asdict(self)


CONFIG_PATH = Path.home() / ".chroma_walnut_ui" / "connections.json"

ChromaClient = Union[chromadb.HttpClient, chromadb.PersistentClient]


class ChromaManager:
    def __init__(self):
        self._connections: dict[str, ConnectionConfig] = {}
        self._clients: dict[str, ChromaClient] = {}
        self._load()

    def _load(self):
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            for item in data:
                if "conn_type" not in item:
                    item["conn_type"] = "http"
                if "path" not in item:
                    item["path"] = ""
                # 移除旧版连接级 embedding 字段
                for old_key in ("embedding_url", "embedding_model", "embedding_api_key"):
                    item.pop(old_key, None)
                cfg = ConnectionConfig(**{k: v for k, v in item.items() if k in ConnectionConfig.__dataclass_fields__})
                self._connections[cfg.id] = cfg

    def _save(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps([c.to_dict() for c in self._connections.values()], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_connections(self) -> list[dict]:
        result = []
        for cfg in self._connections.values():
            d = cfg.to_dict()
            d["connected"] = cfg.id in self._clients
            result.append(d)
        return result

    def get_connection(self, conn_id: str):
        return self._connections.get(conn_id)

    def add_connection(self, name: str, conn_type: str, host: str, port: int, is_local: bool, path: str, token: str = "") -> dict:
        cfg = ConnectionConfig(
            id=str(uuid.uuid4()),
            name=name, conn_type=conn_type,
            host=host, port=port, is_local=is_local, path=path, token=token,
        )
        self._connections[cfg.id] = cfg
        self._save()
        d = cfg.to_dict()
        d["connected"] = False
        return d

    def update_connection(self, conn_id: str, name: str, conn_type: str, host: str, port: int, is_local: bool, path: str, token: str = "") -> dict:
        if conn_id not in self._connections:
            return {"success": False, "error": "连接不存在"}
        self.disconnect(conn_id)
        cfg = self._connections[conn_id]
        cfg.name = name
        cfg.conn_type = conn_type
        cfg.host = host
        cfg.port = port
        cfg.is_local = is_local
        cfg.path = path
        cfg.token = token
        self._save()
        d = cfg.to_dict()
        d["connected"] = False
        return d

    def remove_connection(self, conn_id: str) -> bool:
        if conn_id not in self._connections:
            return False
        self.disconnect(conn_id)
        del self._connections[conn_id]
        self._save()
        return True

    def connect(self, conn_id: str) -> dict:
        cfg = self._connections.get(conn_id)
        if not cfg:
            return {"success": False, "error": "连接不存在"}
        try:
            if cfg.conn_type == "persistent":
                if not cfg.path:
                    return {"success": False, "error": "未指定本地目录路径"}
                client = chromadb.PersistentClient(path=cfg.path)
            else:
                headers = {"Authorization": f"Bearer {cfg.token}"} if cfg.token else {}
                client = chromadb.HttpClient(host=cfg.host, port=cfg.port, headers=headers)
                client.heartbeat()
            self._clients[conn_id] = client
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def disconnect(self, conn_id: str):
        self._clients.pop(conn_id, None)

    def get_client(self, conn_id: str) -> ChromaClient:
        client = self._clients.get(conn_id)
        if not client:
            raise ValueError(f"连接 {conn_id} 未建立，请先连接")
        return client


# ── 模块级单例：所有 feature bridge 共享同一个管理器 ─────────────────────────

_manager: ChromaManager | None = None


def get_chroma_manager() -> ChromaManager:
    global _manager
    if _manager is None:
        _manager = ChromaManager()
    return _manager


async def run_blocking(fn, *args, **kwargs):
    """在线程池中执行阻塞调用（chromadb / 网络 I/O），避免阻塞事件循环。"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, functools.partial(fn, *args, **kwargs))
