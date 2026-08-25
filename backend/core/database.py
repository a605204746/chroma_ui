import asyncio
import os

import aiosqlite
from loguru import logger

# SQLite 写锁超时后的重试参数
_RETRY_COUNT    = 3
_RETRY_BASE_MS  = 50   # 首次重试等待 50ms，之后指数退避


class Database:
    """
    异步 SQLite 连接封装，管理连接生命周期。
    多个 Service 共享同一实例时，用 ensure_open() 代替 open()，可安全并发调用。

    并发策略：
    - 开启 WAL 模式，允许读写并发
    - 写操作通过 _write_lock 串行化，避免 "database is locked"
    - 写失败时自动重试（指数退避）
    """

    def __init__(self, path: str | None = None):
        self._conn: aiosqlite.Connection | None = None
        self._path: str | None = None
        self._default_path: str | None = path
        self._open_lock: asyncio.Lock | None = None
        self._write_lock: asyncio.Lock | None = None

    def _get_open_lock(self) -> asyncio.Lock:
        if self._open_lock is None:
            self._open_lock = asyncio.Lock()
        return self._open_lock

    def _get_write_lock(self) -> asyncio.Lock:
        if self._write_lock is None:
            self._write_lock = asyncio.Lock()
        return self._write_lock

    @property
    def is_open(self) -> bool:
        return self._conn is not None

    @property
    def path(self) -> str | None:
        return self._path

    async def open(self, path: str) -> None:
        await self.close()
        self._conn = await aiosqlite.connect(path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA busy_timeout=5000")
        self._path = path

    async def ensure_open(self, path: str | None = None) -> None:
        """并发安全打开：已连接则直接返回，多个 Bridge 共享时不会重复打开。"""
        async with self._get_open_lock():
            if self._conn is not None:
                return
            p = path or self._default_path
            if not p:
                raise RuntimeError("未指定数据库路径，请传入 path 或在 Database(path=...) 中设置。")
            os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
            self._conn = await aiosqlite.connect(p)
            self._conn.row_factory = aiosqlite.Row
            # WAL 模式：读写并发，写不阻塞读
            await self._conn.execute("PRAGMA journal_mode=WAL")
            # busy_timeout：SQLite 内部遇到锁时等待 5 秒再报错
            await self._conn.execute("PRAGMA busy_timeout=5000")
            self._path = p

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None
            self._path = None

    # ── 读操作（无需额外锁，WAL 模式下读写可并发） ──

    async def fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        self._ensure_open()
        async with self._conn.execute(sql, params) as cur:
            rows = await cur.fetchall()
            return [dict(row) for row in rows]

    async def fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        self._ensure_open()
        async with self._conn.execute(sql, params) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def fetchpage(
        self, sql: str, params: tuple = (), page: int = 1, page_size: int = 50
    ) -> tuple[list[dict], list[str]]:
        self._ensure_open()
        offset = (page - 1) * page_size
        paged_sql = f"{sql} LIMIT ? OFFSET ?"
        async with self._conn.execute(paged_sql, (*params, page_size, offset)) as cur:
            rows = await cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return [dict(row) for row in rows], columns

    async def count(self, table: str) -> int:
        row = await self.fetchone(f'SELECT COUNT(*) AS n FROM "{table}"')
        return row["n"] if row else 0

    # ── 写操作（通过 _write_lock 串行化 + 重试） ──

    async def execute(self, sql: str, params: tuple = ()) -> int:
        self._ensure_open()
        async with self._get_write_lock():
            return await self._execute_with_retry(sql, params)

    async def executescript(self, sql: str) -> None:
        self._ensure_open()
        async with self._get_write_lock():
            await self._conn.executescript(sql)

    async def _execute_with_retry(self, sql: str, params: tuple = ()) -> int:
        """写操作带重试：遇到 locked 时指数退避重试。"""
        last_err = None
        for attempt in range(_RETRY_COUNT):
            try:
                async with self._conn.execute(sql, params) as cur:
                    await self._conn.commit()
                    return cur.rowcount
            except Exception as e:
                last_err = e
                err_msg = str(e).lower()
                if "locked" in err_msg or "busy" in err_msg:
                    wait_ms = _RETRY_BASE_MS * (2 ** attempt)
                    logger.debug(
                        "数据库写锁定，第 {} 次重试（等待 {}ms）: {}",
                        attempt + 1, wait_ms, e,
                    )
                    await asyncio.sleep(wait_ms / 1000)
                else:
                    raise
        raise last_err  # type: ignore[misc]

    # ── 上下文管理器 ──

    async def __aenter__(self) -> "Database":
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    def _ensure_open(self) -> None:
        if not self._conn:
            raise RuntimeError("数据库未打开，请先调用 open(path)。")
