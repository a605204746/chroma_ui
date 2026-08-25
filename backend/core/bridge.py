_DEFAULT_TIMEOUT = 15  # 秒，适用于未声明超时的方法


def exposed(func=None, *, name: str = None, timeout: int = _DEFAULT_TIMEOUT):
    """
    将方法标记为可从 JS 调用的桥接方法。

    用法：
        @exposed
        def get_version(self) -> str: ...

        @exposed(name="customName")
        def internal_method(self): ...

        @exposed(timeout=60)
        async def export_data(self) -> dict: ...   # 长任务放宽超时
    """
    def decorator(fn):
        fn._is_exposed = True
        fn._exposed_name = name or fn.__name__
        fn._timeout = timeout
        return fn

    if func is not None:
        return decorator(func)
    return decorator


class BridgeMeta(type):
    """元类：在类创建时扫描所有 @exposed 方法，构建路由表。"""
    def __new__(mcs, name, bases, namespace):
        exposed_methods = {}
        for val in namespace.values():
            if callable(val) and getattr(val, "_is_exposed", False):
                exposed_methods[val._exposed_name] = val

        for base in bases:
            if hasattr(base, "_exposed_methods"):
                for k, v in base._exposed_methods.items():
                    if k not in exposed_methods:
                        exposed_methods[k] = v

        namespace["_exposed_methods"] = exposed_methods
        return super().__new__(mcs, name, bases, namespace)


class Bridge(metaclass=BridgeMeta):
    """
    所有业务桥接器的基类。

    子类用 @exposed 标注方法，框架自动处理参数反序列化、结果序列化、错误捕获。

    Python 主动推送事件给 JS：
        self.push_event("themeChanged", {"theme": "dark"})
    """

    def __init__(self):
        self._bridge_name: str = ""
        self._push_fn = None  # 由 PywebviewApi.register() 注入

    def _set_push_fn(self, fn) -> None:
        self._push_fn = fn

    def push_event(self, event_or_name, payload=None, *, urgent: bool = False) -> None:
        """Python 主动推送事件给 JS 端。

        event_or_name 可以是 @event 装饰的 TypedDict 类，或直接传事件名字符串。
        urgent=True 跳过攒批等待窗口，立即推送（适用于状态变更类一次性事件）。
        """
        if not self._push_fn:
            return
        name = getattr(event_or_name, "__event_name__", event_or_name)
        self._push_fn(self._bridge_name, name, payload if payload is not None else {}, urgent=urgent)

    def on_registered(self) -> None:
        """注册后由框架自动调用。"""
        pass

    def on_shutdown(self) -> None:
        """窗口关闭时由框架调用，子类可重写以释放资源。"""
        pass

    @property
    def bridge_name(self) -> str:
        return self._bridge_name
