import asyncio
import threading

import webview
from loguru import logger

from .bridge import Bridge
from .channel import MessageQueue, PywebviewApi
from .config import AppConfig
from .database import Database
from .window import create_window


class Application:
    """
    顶层应用封装，简化启动流程。

    用法：
        app = Application(config, dev_mode="--dev" in sys.argv, db=shared_db)
        app.register_bridge("system", system_bridge)
        sys.exit(app.run())
    """

    def __init__(self, config: AppConfig, dev_mode: bool = False, db: Database | None = None):
        self._config = config
        self._dev_mode = dev_mode
        self._db = db

        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._loop.run_forever,
            daemon=True,
            name="app-asyncio",
        )
        self._loop_thread.start()

        self._msg_queue = MessageQueue()
        self.api = PywebviewApi(self._loop, self._msg_queue, debug=dev_mode)
        self._window: webview.Window | None = None

    def register_bridge(self, name: str, bridge: Bridge) -> "Application":
        self.api.register(name, bridge)
        return self

    def run(self) -> int:
        self._window = create_window(self._config.window, self._dev_mode, self.api)

        def on_loaded():
            self._msg_queue.set_window(self._window)
            logger.info("前端已加载，消息通道就绪")

        self._window.events.loaded += on_loaded
        self._window.events.closing += self._shutdown

        logger.info("启动 pywebview（dev={}）", self._dev_mode)
        webview.start(
            debug=self._dev_mode,
            icon=self._config.window.icon or None,
        )
        return 0

    def _shutdown(self) -> None:
        logger.info("正在清理资源…")

        self.api.shutdown_all()

        if self._db is not None:
            try:
                fut = asyncio.run_coroutine_threadsafe(self._db.close(), self._loop)
                fut.result(timeout=5)
            except Exception as e:
                logger.warning("数据库关闭异常: {}", e)

        self._loop.call_soon_threadsafe(self._loop.stop)
        logger.info("资源清理完成")
