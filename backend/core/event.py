_registry: dict[str, type] = {}


def event(name: str):
    """把事件名挂到 TypedDict 上，并注册到全局表。

    用法：
        @event("notification")
        class Notification(TypedDict):
            id: int
            title: str

        # 函数式 TypedDict（字段名含 Python 关键字时）：
        TestEvent = TypedDict("TestEvent", {"message": str, "from": str})
        event("testEvent")(TestEvent)
    """
    def deco(cls: type) -> type:
        if name in _registry:
            existing = _registry[name]
            raise ValueError(
                f"事件名 '{name}' 已被 {existing.__module__}.{existing.__qualname__} 注册，"
                f"无法再被 {cls.__module__}.{cls.__qualname__} 使用"
            )
        cls.__event_name__ = name  # type: ignore[attr-defined]
        _registry[name] = cls
        return cls
    return deco
