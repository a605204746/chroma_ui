import asyncio
import concurrent.futures
import inspect
import queue
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from loguru import logger

from .bridge import Bridge


# ── JSON 序列化（支持常见 Python 类型） ──

def _json_default(obj):
    """自定义序列化器：处理 datetime/Decimal/Enum/UUID/bytes 等。"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


try:
    import orjson

    def _dumps(obj: object) -> str:
        return orjson.dumps(obj, default=_json_default).decode()

except ImportError:
    import json

    def _dumps(obj: object) -> str:
        return json.dumps(obj, ensure_ascii=False, default=_json_default)


class MessageQueue:
    """
    线程安全的批量消息队列，将 Python 事件攒批后通过 evaluate_js 推送给前端。

    线程安全策略：
    - _window_lock 保护 _window 的读写
    - shutdown 时显式清空 _window，等待 flush 完成
    - evaluate_js 前再次检查 _window 是否有效

    性能优化：
    - 专用 flush 线程（Condition.wait，无线程创建开销）
    - 非阻塞 evaluate_js（ThreadPoolExecutor(1)）
    - urgent=True：跳过等待窗口立即唤醒 flush
    - orjson：若已安装则使用，序列化比标准库快 5-10 倍
    """

    _INTERVAL   = 0.1
    _MAX_BATCH  = 50
    _MAX_QUEUE  = 500

    def __init__(self):
        self._queue   = queue.Queue(maxsize=self._MAX_QUEUE)
        self._cond    = threading.Condition()
        self._window  = None
        self._stopped = False
        self._window_lock = threading.Lock()  # 保护 _window 的读写

        self._flush_thread = threading.Thread(
            target=self._flush_loop, daemon=True, name="mq-flush"
        )
        self._flush_thread.start()

        self._eval_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mq-eval")

    def set_window(self, window) -> None:
        with self._window_lock:
            self._window = window
        with self._cond:
            self._cond.notify()

    def push(self, bridge_name: str, event_name: str, payload: object, *, urgent: bool = False) -> None:
        try:
            self._queue.put_nowait([bridge_name, event_name, payload])
        except queue.Full:
            logger.warning(
                "MessageQueue 已满（{}条），丢弃事件 {}.{}", self._MAX_QUEUE, bridge_name, event_name
            )
            return
        if urgent or self._queue.qsize() >= self._MAX_BATCH:
            with self._cond:
                self._cond.notify()

    def shutdown(self) -> None:
        with self._window_lock:
            self._window = None  # 显式清空，防止后续 evaluate_js
        with self._cond:
            self._stopped = True
            self._cond.notify()
        # 等待正在执行的 evaluate_js 完成
        self._eval_executor.shutdown(wait=True, cancel_futures=True)

    def _flush_loop(self) -> None:
        while True:
            with self._cond:
                self._cond.wait(timeout=self._INTERVAL)
                stopped = self._stopped
            self._do_flush()
            if stopped:
                break

    def _do_flush(self) -> None:
        with self._window_lock:
            window = self._window
        if window is None:
            return

        items = []
        while len(items) < self._MAX_BATCH:
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                break
        if not items:
            return

        try:
            payload = _dumps(items)
        except Exception as e:
            logger.warning("事件序列化失败: {}", e)
            return

        try:
            self._eval_executor.submit(self._eval_js, window, payload)
        except RuntimeError:
            pass

    def _eval_js(self, window, payload: str) -> None:
        """在线程池中执行，传入 window 快照避免竞态。"""
        try:
            window.evaluate_js(f"window.__pyBatch({payload})")
        except Exception as e:
            logger.warning("evaluate_js 推送失败: {}", e)


class PywebviewApi:
    """
    pywebview 暴露给 JS 的统一 API 对象，聚合所有 Bridge 并路由调用。
    JS 侧通过 window.pywebview.api.dispatch(bridge, method, payload) 调用。

    请求追踪：
    - 每次调用生成唯一 request_id
    - 记录调用耗时
    - 超时后尝试取消协程
    """

    def __init__(self, loop: asyncio.AbstractEventLoop, msg_queue: MessageQueue, debug: bool = False):
        self._loop = loop
        self._msg_queue = msg_queue
        self._debug = debug
        self._bridges: dict[str, Bridge] = {}

    def register(self, name: str, bridge: Bridge) -> "PywebviewApi":
        bridge._bridge_name = name
        bridge._set_push_fn(self._msg_queue.push)
        self._bridges[name] = bridge
        bridge.on_registered()
        return self

    def get_bridge(self, name: str) -> Bridge | None:
        return self._bridges.get(name)

    def shutdown_all(self) -> None:
        for name, bridge in self._bridges.items():
            try:
                bridge.on_shutdown()
            except Exception as e:
                logger.warning("Bridge '{}' on_shutdown 异常: {}", name, e)
        self._msg_queue.shutdown()

    def dispatch(self, bridge_name: str, method_name: str, payload: dict | list | None = None) -> dict:
        """
        JS 调用的统一入口，由 pywebview 在工作线程中调用（非主线程）。

        返回格式：
        {
            "ok": True/False,
            "data": ...,          # 成功时
            "error": "...",       # 失败时
            "traceback": "...",   # debug 模式
            "request_id": "...",  # 请求追踪 ID
        }
        """
        request_id = uuid.uuid4().hex[:8]
        start_time = time.monotonic()

        logger.debug("[{}] → {}.{} payload={}", request_id, bridge_name, method_name, payload)

        try:
            bridge = self._bridges.get(bridge_name)
            if bridge is None:
                return {"ok": False, "error": f"Bridge '{bridge_name}' not found", "request_id": request_id}

            method = bridge._exposed_methods.get(method_name)
            if method is None:
                return {"ok": False, "error": f"Method '{method_name}' not exposed on '{bridge_name}'", "request_id": request_id}

            if payload is None:
                payload = {}
            if isinstance(payload, dict):
                result_or_coro = method(bridge, **payload)
            elif isinstance(payload, list):
                result_or_coro = method(bridge, *payload)
            else:
                return {"ok": False, "error": f"Payload must be object or array, got {type(payload).__name__}", "request_id": request_id}

            if inspect.iscoroutine(result_or_coro):
                timeout = getattr(method, "_timeout", 15)
                future = asyncio.run_coroutine_threadsafe(result_or_coro, self._loop)
                try:
                    result = future.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    # 超时后尝试取消协程
                    self._loop.call_soon_threadsafe(future.cancel)
                    elapsed_ms = (time.monotonic() - start_time) * 1000
                    logger.warning(
                        "[{}] ✗ {}.{} 超时（{}ms，限制 {}s）",
                        request_id, bridge_name, method_name, elapsed_ms, timeout,
                    )
                    return {"ok": False, "error": f"Method '{method_name}' timed out ({timeout}s)", "request_id": request_id}
                except concurrent.futures.CancelledError:
                    elapsed_ms = (time.monotonic() - start_time) * 1000
                    logger.warning("[{}] ✗ {}.{} 已取消（{}ms）", request_id, bridge_name, method_name, elapsed_ms)
                    return {"ok": False, "error": f"Method '{method_name}' was cancelled", "request_id": request_id}
            else:
                result = result_or_coro

            elapsed_ms = (time.monotonic() - start_time) * 1000
            logger.debug("[{}] ← {}.{} {}ms", request_id, bridge_name, method_name, elapsed_ms)
            return {"ok": True, "data": result, "request_id": request_id}

        except Exception as e:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            logger.error("[{}] ✗ {}.{} {}ms error: {}", request_id, bridge_name, method_name, elapsed_ms, e)
            resp: dict = {"ok": False, "error": str(e), "request_id": request_id}
            if self._debug:
                resp["traceback"] = traceback.format_exc()
            return resp
