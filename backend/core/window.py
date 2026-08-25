import json
import os

import webview
from loguru import logger

from .config import WindowConfig
from .paths import resource, userdata

_GEOMETRY_FILE = userdata("data/window_state.json")
DEV_URL = "http://localhost:5173"


def create_window(win_cfg: WindowConfig, dev_mode: bool, api) -> webview.Window:
    """创建 pywebview 窗口，恢复上次几何并绑定关闭时保存。"""
    geo = _load_geometry()
    w = geo.get("width",  win_cfg.width  if win_cfg.width  > 0 else 1200)
    h = geo.get("height", win_cfg.height if win_cfg.height > 0 else 800)
    x = geo.get("x")
    y = geo.get("y")

    url = DEV_URL if dev_mode else resource("frontend/dist/index.html")

    window = webview.create_window(
        title            = win_cfg.title,
        url              = url,
        js_api           = api,
        width            = w,
        height           = h,
        x                = x,
        y                = y,
        min_size         = (win_cfg.min_width, win_cfg.min_height),
        resizable        = win_cfg.resizable,
        frameless        = win_cfg.frameless,
        easy_drag        = win_cfg.easy_drag,
        on_top           = win_cfg.on_top,
        confirm_close    = win_cfg.confirm_close,
        minimized        = win_cfg.minimized,
        maximized        = win_cfg.maximized,
        fullscreen       = win_cfg.fullscreen,
        background_color = win_cfg.background_color,
        transparent      = win_cfg.transparent,
    )

    if win_cfg.remember_geometry:
        window.events.closing += lambda: _save_geometry(window)

    return window


def _load_geometry() -> dict:
    try:
        with open(_GEOMETRY_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_geometry(window: webview.Window) -> None:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(_GEOMETRY_FILE)), exist_ok=True)
        with open(_GEOMETRY_FILE, "w") as f:
            json.dump(
                {"x": window.x, "y": window.y, "width": window.width, "height": window.height},
                f,
            )
        logger.debug("窗口几何已保存: {}x{} @ ({}, {})", window.width, window.height, window.x, window.y)
    except Exception as e:
        logger.warning("保存窗口几何失败：{}", e)
