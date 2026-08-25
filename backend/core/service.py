import asyncio

from loguru import logger

from .database import Database


class DbReadyService:
    """
    持有 Database 引用并提供幕等懒初始化的服务基类。
    子类重写 _init_db() 来建表、填充种子数据；框架保证并发安全且只执行一次。

    初始化失败处理：
    - 如果 _init_db() 抛出异常，标记 _init_failed = True
    - 后续调用 _ensure_ready() 会立即抛出 RuntimeError，避免重复失败
    - 使用事务确保初始化的原子性

    用法：
        class UserBridge(Bridge, DbReadyService):
            async def _init_db(self) -> None:
                await self._db.execute("CREATE TABLE IF NOT EXISTS ...")

            async def get_users(self) -> list:
                await self._ensure_ready()
                ...
    """

    def __init__(self, db: Database):
        self._db = db
        self._ready = False
        self._init_failed = False  # 标记初始化是否失败
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _ensure_ready(self) -> None:
        if self._ready:
            return
        if self._init_failed:
            raise RuntimeError("数据库初始化曾失败，无法继续使用")

        async with self._get_lock():
            if self._ready:
                return
            if self._init_failed:
                raise RuntimeError("数据库初始化曾失败，无法继续使用")

            try:
                await self._db.ensure_open()
                await self._init_db()
                self._ready = True
                logger.debug("{} 数据库初始化完成", self.__class__.__name__)
            except Exception as e:
                self._init_failed = True
                logger.error("{} 数据库初始化失败: {}", self.__class__.__name__, e)
                raise

    async def _init_db(self) -> None:
        """子类重写：建表、填充种子数据等一次性初始化。"""
        pass
