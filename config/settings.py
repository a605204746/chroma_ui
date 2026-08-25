"""应用全局配置 — 窗口、日志等（模板 AppConfig 结构）。"""
import ctypes
import sys

from backend.core.config import AppConfig, DatabaseConfig, LoggingConfig, WindowConfig
from backend.shared.icon import app_icon_path


def _calc_window_geometry() -> tuple[int, int]:
    """根据屏幕分辨率计算默认窗口尺寸，返回 (w, h)。"""
    try:
        # 不设置 DPI 感知，GetSystemMetrics 返回逻辑像素，与 PyWebView 坐标系一致
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        sh = ctypes.windll.user32.GetSystemMetrics(1)
    except Exception:
        return 1200, 760

    if sw <= 1366:
        w = min(int(sw * 0.88), 1200)
        h = min(int(sh * 0.85), 720)
    else:
        w = min(int(sw * 0.75), 1500)
        h = min(int(sh * 0.78), 960)

    return max(w, 900), max(h, 600)


_win_w, _win_h = _calc_window_geometry()

config = AppConfig(
    window=WindowConfig(
        title="Chroma Walnut UI",
        icon=app_icon_path(),
        width=_win_w,
        height=_win_h,
        min_width=900,
        min_height=600,
        remember_geometry=True,
    ),
    # 本项目数据均存放于 ChromaDB / ~/.chroma_walnut_ui，内置 SQLite 保持默认未使用
    database=DatabaseConfig(),
    logging=LoggingConfig(
        level="INFO",
        path="data/logs/app.log",
    ),
)
