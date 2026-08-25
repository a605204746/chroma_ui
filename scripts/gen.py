#!/usr/bin/env python
"""
同步生成前端所有自动代码：

  python scripts/gen.py

生成文件：
  frontend/src/event/_bridges.ts        — BRIDGES 常量
  frontend/src/event/<feature>.ts       — EVENTS 常量 + TS interface
  frontend/src/event/index.ts           — 统一 re-export
  frontend/src/api/<feature>.ts         — xxxApi 对象（扫描 @exposed 方法）
  frontend/src/api/index.ts             — 统一 re-export

TypedDict 注解规则：
  - 返回类型注解为 TypedDict 子类 → 自动生成对应 TS interface
  - 模块级 Union[TypedDict, ...] 变量 → 自动生成 TS type alias
  - TypedDict 嵌套引用 → 按依赖顺序递归生成（被依赖项在前）
"""

import importlib
import inspect
import json
import sys
import types as _types
from pathlib import Path
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

# Python 3.10+ PEP 604 union type (e.g. `str | None`)
_PEP604_UnionType = getattr(_types, "UnionType", None)

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

ROOT         = Path(__file__).resolve().parent.parent
FEATURES_DIR = ROOT / "backend" / "features"
EVENT_TS_DIR = ROOT / "frontend" / "src" / "event"
API_TS_DIR   = ROOT / "frontend" / "src" / "api"

sys.path.insert(0, str(ROOT))


# ─── 工具 ─────────────────────────────────────────────────────────────────────

def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _is_typeddict(tp: Any) -> bool:
    return (
        isinstance(tp, type)
        and issubclass(tp, dict)
        and hasattr(tp, "__required_keys__")
        and hasattr(tp, "__optional_keys__")
    )


# ─── 类型转换 ─────────────────────────────────────────────────────────────────

def _py_to_ts(tp: Any) -> str:
    """Python type → TypeScript type string."""
    if tp is str:          return "string"
    if tp is int:          return "number"
    if tp is float:        return "number"
    if tp is bool:         return "boolean"
    if tp is type(None):   return "null"
    if tp is Any:          return "unknown"  # type: ignore[comparison-overlap]
    if tp is dict:         return "unknown"
    if tp is list:         return "unknown[]"
    if tp is bytes:        return "string"
    if _is_typeddict(tp):  return tp.__name__

    # Python 3.10+ `str | None` syntax → types.UnionType
    if _PEP604_UnionType is not None and isinstance(tp, _PEP604_UnionType):
        args_pep = get_args(tp)
        non_none = [a for a in args_pep if a is not type(None)]
        has_none = any(a is type(None) for a in args_pep)
        ts = " | ".join(_py_to_ts(a) for a in non_none)
        return (ts + " | null") if has_none else ts

    origin = get_origin(tp)
    args   = get_args(tp)

    if origin is Literal:
        return " | ".join(
            f'"{a}"' if isinstance(a, str) else str(a).lower()
            for a in args
        )
    if origin is list:
        return f"{_py_to_ts(args[0]) if args else 'unknown'}[]"
    if origin is Union:
        non_none = [a for a in args if a is not type(None)]
        has_none = any(a is type(None) for a in args)
        ts = " | ".join(_py_to_ts(a) for a in non_none)
        return (ts + " | null") if has_none else ts
    if origin is dict:
        k = _py_to_ts(args[0]) if args else "string"
        v = _py_to_ts(args[1]) if len(args) > 1 else "unknown"
        return f"Record<{k}, {v}>"

    name = getattr(tp, "__name__", None)
    return name if name else "unknown"


def _py_to_ts_return(tp: Any) -> str:
    """Like _py_to_ts but None/NoneType → 'void' (for return type annotations)."""
    if tp is None or tp is type(None) or tp is inspect.Parameter.empty:
        return "void"
    return _py_to_ts(tp)


# ─── TypedDict → TS interface ─────────────────────────────────────────────────

def _render_interface(name: str, cls: type) -> str:
    try:
        hints = get_type_hints(cls)
    except Exception:
        hints = dict(getattr(cls, "__annotations__", {}))
    required: frozenset = getattr(cls, "__required_keys__", frozenset(hints))
    lines = [f"export interface {name} {{"]
    for field, tp in hints.items():
        opt = "" if field in required else "?"
        lines.append(f"  {field}{opt}: {_py_to_ts(tp)};")
    lines.append("}")
    return "\n".join(lines)


# ─── 递归收集 TypedDict（依赖优先 DFS 后序） ──────────────────────────────────

def _collect_typedicts_ordered(
    tp: Any,
    seen: set | None = None,
    result: list | None = None,
) -> list[tuple[str, type]]:
    """返回 [(name, cls), ...] — 被依赖的 TypedDict 在前（后序 DFS）。"""
    if seen is None:
        seen = set()
    if result is None:
        result = []
    if tp is None:
        return result

    if _is_typeddict(tp):
        if id(tp) in seen:
            return result
        seen.add(id(tp))
        # 先递归字段类型
        try:
            hints = get_type_hints(tp)
        except Exception:
            hints = {}
        for field_tp in hints.values():
            _collect_typedicts_ordered(field_tp, seen, result)
        result.append((tp.__name__, tp))
        return result

    # 容器 / Union / PEP 604 union：递归 args
    args = get_args(tp)
    for a in args:
        _collect_typedicts_ordered(a, seen, result)
    return result


# ─── 收集模块级 Union[TypedDict, ...] 作为 TS type alias ──────────────────────

def _find_module_type_aliases(mod: Any) -> dict[str, str]:
    """
    查找模块级 Union[TypedDictA, TypedDictB, ...] 变量，
    生成 export type Foo = A | B | C; 语句。
    """
    aliases: dict[str, str] = {}
    for name, val in vars(mod).items():
        if name.startswith("_"):
            continue
        if _is_typeddict(val):
            continue
        origin = get_origin(val)
        if origin is Union:
            non_none = [a for a in get_args(val) if a is not type(None)]
            if non_none and all(_is_typeddict(a) for a in non_none):
                aliases[name] = _py_to_ts(val)
    return aliases


# ─── 参数默认值 ───────────────────────────────────────────────────────────────

def _default_to_ts(val: Any) -> str | None:
    if val is inspect.Parameter.empty:
        return None
    if val is None:
        return "undefined"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        return json.dumps(val)
    return None


# ─── BRIDGES ─────────────────────────────────────────────────────────────────

def gen_bridges() -> list[str]:
    bridges: list[str] = []
    for bridge_path in sorted(FEATURES_DIR.glob("*/bridge.py")):
        feature = bridge_path.parent.name
        mod = importlib.import_module(f"backend.features.{feature}.bridge")
        has_bridge = any(
            isinstance(obj, type)
            and attr.endswith("Bridge")
            and hasattr(obj, "_exposed_methods")
            and obj._exposed_methods
            for attr, obj in vars(mod).items()
        )
        if has_bridge:
            bridges.append(feature)
    bridges.sort()

    lines = [
        "// 此文件由 gen.py 自动生成，请勿手动修改。\n",
        "export const BRIDGES = {",
    ]
    for b in bridges:
        lines.append(f'  {b}: "{b}",')
    lines.append("} as const;")
    (EVENT_TS_DIR / "_bridges.ts").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  _bridges.ts  →  BRIDGES: [{', '.join(bridges)}]")
    return bridges


# ─── EVENTS ──────────────────────────────────────────────────────────────────

def gen_events() -> dict[str, list[str]]:
    from backend.core.event import _registry  # noqa: PLC0415

    all_exports: dict[str, list[str]] = {}

    for events_path in sorted(FEATURES_DIR.glob("*/events.py")):
        feature  = events_path.parent.name
        mod_name = f"backend.features.{feature}.events"
        importlib.import_module(mod_name)

        module_events: dict[str, type] = {
            ename: cls
            for ename, cls in _registry.items()
            if getattr(cls, "__module__", "") == mod_name
        }
        if not module_events:
            continue

        const_lines = ["export const EVENTS = {"]
        for ename in module_events:
            const_lines.append(f'  {ename}: "{ename}",')
        const_lines.append("} as const;")

        td_seen: set = set()
        td_list: list[tuple[str, type]] = []
        for cls in module_events.values():
            _collect_typedicts_ordered(cls, td_seen, td_list)

        interfaces = [_render_interface(name, cls) for name, cls in td_list]
        names = [name for name, _ in td_list]

        header = (
            "// 此文件由 gen.py 自动生成，请勿手动修改。\n"
            f"// 源定义：backend/features/{feature}/events.py\n"
        )
        body = "\n".join(const_lines) + "\n\n" + "\n\n".join(interfaces) + "\n"
        (EVENT_TS_DIR / f"{feature}.ts").write_text(header + "\n" + body, encoding="utf-8")

        all_exports[feature] = names
        print(f"  {feature}/events.py  →  {feature}.ts  [{', '.join(names)}]")

    return all_exports


def gen_event_index(all_exports: dict[str, list[str]]) -> None:
    lines = ["// 此文件由 gen.py 自动生成，请勿手动修改。\n"]
    lines.append('export { BRIDGES } from "@/event/_bridges";')
    for feature, names in all_exports.items():
        lines.append(f'export {{ EVENTS as {feature}Events }} from "@/event/{feature}";')
        lines.append(f'export type {{ {", ".join(names)} }} from "@/event/{feature}";')
    (EVENT_TS_DIR / "index.ts").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("  event/index.ts")


# ─── API ──────────────────────────────────────────────────────────────────────

def gen_api() -> None:
    # feature → 该文件导出的所有类型名称（interface + type alias）
    api_type_exports: dict[str, list[str]] = {}

    for bridge_path in sorted(FEATURES_DIR.glob("*/bridge.py")):
        feature = bridge_path.parent.name
        mod     = importlib.import_module(f"backend.features.{feature}.bridge")

        bridge_cls = None
        for attr, obj in vars(mod).items():
            if (isinstance(obj, type) and attr.endswith("Bridge")
                    and hasattr(obj, "_exposed_methods") and obj._exposed_methods):
                bridge_cls = obj
                break
        if bridge_cls is None:
            continue

        td_seen: set         = set()
        td_list: list        = []   # [(name, cls), ...]
        method_lines: list   = []
        exposed_names: list  = []

        for exposed_name, method in bridge_cls._exposed_methods.items():
            try:
                hints = get_type_hints(method)
            except Exception:
                hints = {}

            return_hint = hints.get("return")
            return_ts   = _py_to_ts_return(return_hint)
            _collect_typedicts_ordered(return_hint, td_seen, td_list)

            sig          = inspect.signature(method)
            ts_params:   list = []
            payload_keys: list = []

            for pname, param in sig.parameters.items():
                if pname == "self":
                    continue
                hint    = hints.get(pname)
                ts_type = _py_to_ts(hint) if hint is not None else "unknown"
                default = _default_to_ts(param.default)
                if default is not None:
                    ts_params.append(f"{pname}: {ts_type} = {default}")
                else:
                    ts_params.append(f"{pname}: {ts_type}")
                payload_keys.append(pname)

            camel     = _to_camel(exposed_name)
            param_str = ", ".join(ts_params)
            if payload_keys:
                payload = "{ " + ", ".join(payload_keys) + " }"
                invoke  = f'await _proxy.invoke<{return_ts}>("{exposed_name}", {payload})'
            else:
                invoke  = f'await _proxy.invoke<{return_ts}>("{exposed_name}")'

            method_lines.append(f"  {camel}: async ({param_str}) =>\n    {invoke},")
            exposed_names.append(exposed_name)

        # 模块级 Union 类型别名（如 SqlResult = Union[A, B, C]）
        type_aliases = _find_module_type_aliases(mod)
        for alias_val in (vars(mod)[n] for n in type_aliases):
            _collect_typedicts_ordered(alias_val, td_seen, td_list)

        # 组装文件内容
        exported_types: list[str] = []
        parts: list[str] = [
            "// 此文件由 gen.py 自动生成，请勿手动修改。",
            f"// 源定义：backend/features/{feature}/bridge.py",
            "",
            'import { getProxy } from "@/bridge";',
        ]

        if td_list or type_aliases:
            parts.append("")
            for td_name, td_cls in td_list:
                parts.append(_render_interface(td_name, td_cls))
                parts.append("")
                exported_types.append(td_name)
            for alias_name, alias_ts in type_aliases.items():
                parts.append(f"export type {alias_name} = {alias_ts};")
                parts.append("")
                exported_types.append(alias_name)

        api_name = _to_camel(feature) + "Api"
        parts += [
            f'const _proxy = getProxy("{feature}");',
            "",
            f"export const {api_name} = {{",
            *method_lines,
            "};",
        ]

        (API_TS_DIR / f"{feature}.ts").write_text("\n".join(parts) + "\n", encoding="utf-8")
        api_type_exports[feature] = exported_types
        print(f"  {feature}/bridge.py  →  {feature}.ts  [{', '.join(exposed_names)}]")

    # api/index.ts
    idx: list[str] = ["// 此文件由 gen.py 自动生成，请勿手动修改。", ""]
    for feature in sorted(api_type_exports):
        api_name = _to_camel(feature) + "Api"
        idx.append(f'export {{ {api_name} }} from "@/api/{feature}";')
        types = api_type_exports[feature]
        if types:
            idx.append(f'export type {{ {", ".join(types)} }} from "@/api/{feature}";')
    (API_TS_DIR / "index.ts").write_text("\n".join(idx) + "\n", encoding="utf-8")
    print("  api/index.ts")


# ─── 入口 ─────────────────────────────────────────────────────────────────────

def main() -> None:
    EVENT_TS_DIR.mkdir(parents=True, exist_ok=True)
    API_TS_DIR.mkdir(parents=True, exist_ok=True)

    print("── bridges ──")
    gen_bridges()
    print("── events ───")
    gen_event_index(gen_events())
    print("── api ──────")
    gen_api()
    print("\n完成！frontend/src/event/ 和 frontend/src/api/ 已全部更新。")


if __name__ == "__main__":
    main()
