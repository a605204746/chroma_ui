"""连接管理 — ChromaDB 连接的增删改查、测试与连接/断开。"""
from typing import Literal, TypedDict

import webview
from loguru import logger

from backend.core.bridge import Bridge, exposed
from backend.shared.chroma import ChromaManager, run_blocking


class Connection(TypedDict):
    id: str
    name: str
    conn_type: Literal["http", "persistent"]
    host: str
    port: int
    is_local: bool
    path: str
    token: str
    connected: bool


class _ConnOpBase(TypedDict):
    success: bool


class ConnectionOpResult(_ConnOpBase, total=False):
    error: str


class ConnectionBridge(Bridge):

    def __init__(self, mgr: ChromaManager):
        super().__init__()
        self._mgr = mgr

    @exposed
    async def get_connections(self) -> list[Connection]:
        return self._mgr.list_connections()

    @exposed
    async def add_connection(self, name: str, conn_type: str, host: str, port: int,
                             is_local: bool, path: str, token: str = "") -> Connection:
        result = self._mgr.add_connection(name, conn_type, host, int(port), is_local, path, token)
        logger.info("Connection added: name={} type={}", name, conn_type)
        return result

    @exposed
    async def update_connection(self, conn_id: str, name: str, conn_type: str, host: str,
                                port: int, is_local: bool, path: str, token: str = "") -> Connection:
        result = self._mgr.update_connection(conn_id, name, conn_type, host, int(port), is_local, path, token)
        logger.info("Connection updated: conn={} name={}", conn_id, name)
        return result

    @exposed
    async def remove_connection(self, conn_id: str) -> bool:
        result = self._mgr.remove_connection(conn_id)
        logger.info("Connection removed: conn={}", conn_id)
        return result

    @exposed(timeout=30)
    async def test_connection(self, conn_type: str, host: str, port: int,
                              path: str, token: str = "") -> ConnectionOpResult:
        return await run_blocking(self._test_connection, conn_type, host, port, path, token)

    @staticmethod
    def _test_connection(conn_type: str, host: str, port: int, path: str, token: str) -> dict:
        import chromadb
        try:
            if conn_type == "persistent":
                if not path:
                    return {"success": False, "error": "未指定本地目录路径"}
                chromadb.PersistentClient(path=path)
            else:
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                client = chromadb.HttpClient(host=host, port=int(port), headers=headers)
                client.heartbeat()
            logger.info("Connection test OK: type={} host={} port={}", conn_type, host, port)
            return {"success": True}
        except Exception as e:
            logger.warning("Connection test failed: type={} host={} port={} error={}", conn_type, host, port, e)
            return {"success": False, "error": str(e)}

    @exposed(timeout=30)
    async def connect(self, conn_id: str) -> ConnectionOpResult:
        result = await run_blocking(self._mgr.connect, conn_id)
        if result.get("success"):
            logger.info("Connected: conn={}", conn_id)
        else:
            logger.warning("Connect failed: conn={} error={}", conn_id, result.get("error"))
        return result

    @exposed
    async def disconnect(self, conn_id: str) -> bool:
        self._mgr.disconnect(conn_id)
        logger.info("Disconnected: conn={}", conn_id)
        return True

    @exposed(timeout=300)
    async def pick_directory(self) -> str | None:
        """打开系统目录选择对话框（阻塞等待用户选择，故超时放宽）。"""
        def _pick():
            windows = webview.windows
            if not windows:
                return None
            result = windows[0].create_file_dialog(webview.FileDialog.FOLDER)
            if result and len(result) > 0:
                return result[0]
            return None

        return await run_blocking(_pick)
