"""Chroma Walnut UI 入口。

运行方式：
    uv run main.py          # 生产模式：先构建前端再打开窗口
    uv run main.py --dev    # 开发模式：自动启动 Vite dev server（热更新）

冻结模式（PyInstaller 打包后）自动使用打包进 bundle 的 frontend/dist。
"""
import socket
import subprocess
import sys
import time
import traceback

# ── 冻结模式（PyInstaller）适配 ───────────────────────────────────────────────
_FROZEN = getattr(sys, "frozen", False)

# ── 单实例锁 ──────────────────────────────────────────────────────────────────
# Windows：命名互斥量（端口绑定可能撞上 Hyper-V 动态保留端口段，导致误判）
# 其他平台：绑定本地端口，进程退出时自动释放
_INSTANCE_PORT = 19527
_MUTEX_NAME = "ChromaWalnutUI_SingleInstance"
_instance_sock: socket.socket | None = None
_instance_mutex = None  # Windows mutex handle


def _acquire_instance_lock() -> bool:
    """尝试获取单实例锁，返回 True 表示成功（当前是唯一实例）。"""
    global _instance_sock, _instance_mutex

    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
            if handle and kernel32.GetLastError() != 183:  # ERROR_ALREADY_EXISTS
                _instance_mutex = handle  # 持有句柄直到进程退出
                return True
            if handle:
                kernel32.CloseHandle(handle)
            return False
        except Exception:
            pass  # 互斥量异常时退回端口方案

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        s.bind(("127.0.0.1", _INSTANCE_PORT))
        s.listen(1)
        _instance_sock = s
        return True
    except OSError:
        return False


# ── Vite dev server / 前端构建 ────────────────────────────────────────────────

_vite_proc: subprocess.Popen | None = None


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def start_vite() -> None:
    global _vite_proc

    from pathlib import Path
    from loguru import logger

    frontend_dir = Path(__file__).parent / "frontend"
    logger.info("Starting Vite dev server")
    _vite_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True,
    )
    deadline = time.time() + 30
    while time.time() < deadline:
        if _port_open("localhost", 5173):
            logger.info("Vite dev server ready → http://localhost:5173")
            return
        time.sleep(0.3)

    if _vite_proc.poll() is not None:
        logger.error("Vite dev server failed to start")
        sys.exit(1)
    logger.warning("Timed out waiting for Vite, proceeding anyway")


def stop_vite() -> None:
    from loguru import logger

    if _vite_proc and _vite_proc.poll() is None:
        _vite_proc.terminate()
        logger.info("Vite dev server stopped")


def build_frontend() -> None:
    from pathlib import Path
    from loguru import logger

    frontend_dir = Path(__file__).parent / "frontend"
    logger.info("Building frontend")
    result = subprocess.run(["npm", "run", "build"], cwd=frontend_dir, shell=True)
    if result.returncode != 0:
        logger.error("Frontend build failed")
        sys.exit(1)
    logger.info("Frontend build complete")


def main() -> int:
    if not _acquire_instance_lock():
        print("Chroma Walnut UI 已在运行中，请勿重复打开。")
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "Chroma Walnut UI 已在运行中，请勿重复打开。",
                    "Chroma Walnut UI",
                    0x30,  # MB_ICONWARNING
                )
            except Exception:
                pass
        return 0

    # 冻结模式下 --dev 无效（打包产物里没有 Vite）
    dev_mode = "--dev" in sys.argv and not _FROZEN

    from backend.core.log import setup_logging
    from config.settings import config

    setup_logging(config.logging)

    from loguru import logger

    # 屏蔽 chromadb / httpx 等第三方库的 DEBUG 噪音
    import logging
    for noisy in ("chromadb", "httpx", "httpcore", "urllib3", "werkzeug"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # 打包后捕获未处理异常写入日志
    if _FROZEN:
        def _excepthook(exc_type, exc_val, exc_tb):
            logger.opt(exception=(exc_type, exc_val, exc_tb)).critical("Uncaught exception")
        sys.excepthook = _excepthook

    try:
        if dev_mode:
            start_vite()
        elif not _FROZEN:
            build_frontend()

        from backend.core.app import Application
        from backend.features.collection.bridge import CollectionBridge
        from backend.features.connection.bridge import ConnectionBridge
        from backend.features.document.bridge import DocumentBridge
        from backend.features.embedding.bridge import EmbeddingBridge
        from backend.features.query.bridge import QueryBridge
        from backend.shared.chroma import get_chroma_manager

        mgr = get_chroma_manager()

        app = Application(config, dev_mode=dev_mode)

        (app
         .register_bridge("connection", ConnectionBridge(mgr))
         .register_bridge("collection", CollectionBridge(mgr))
         .register_bridge("document",   DocumentBridge(mgr))
         .register_bridge("query",      QueryBridge(mgr))
         .register_bridge("embedding",  EmbeddingBridge(mgr))
        )

        logger.info("所有模块已就绪，启动窗口（dev={}）", dev_mode)
        return app.run()
    except Exception:
        from loguru import logger as _logger
        _logger.exception("Fatal error in main()")
        raise
    finally:
        if dev_mode:
            stop_vite()


if __name__ == "__main__":
    sys.exit(main())
