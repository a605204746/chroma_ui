import subprocess
import sys
import traceback
import time
import socket
from pathlib import Path

# ── 冻结模式（PyInstaller）适配 ───────────────────────────────────────────────
_FROZEN = getattr(sys, 'frozen', False)
_BASE_DIR = Path(sys._MEIPASS) if _FROZEN else Path(__file__).parent

# 最早初始化日志（冻结和开发模式统一）
from logger import setup_logging, get_logger
_dev_mode = "--dev" in sys.argv
setup_logging(debug=_dev_mode)
log = get_logger("main")

# 打包后捕获未处理异常写入日志
if _FROZEN:
    def _excepthook(exc_type, exc_val, exc_tb):
        log.critical("Uncaught exception", exc_info=(exc_type, exc_val, exc_tb))
    sys.excepthook = _excepthook

import webview
from api import API
from icon_utils import apply_window_icon

DEV_URL = "http://localhost:5173"
FRONTEND_DIR = _BASE_DIR / "frontend"
DIST_INDEX = FRONTEND_DIR / "dist" / "index.html"
_vite_proc: subprocess.Popen | None = None


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def start_vite() -> None:
    global _vite_proc
    src_frontend = Path(__file__).parent / "frontend"
    log.info("Starting Vite dev server")
    _vite_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=src_frontend,
        shell=True,
    )
    deadline = time.time() + 30
    while time.time() < deadline:
        if _port_open("localhost", 5173):
            log.info("Vite dev server ready → http://localhost:5173")
            return
        time.sleep(0.3)

    if _vite_proc.poll() is not None:
        log.error("Vite dev server failed to start")
        sys.exit(1)
    log.warning("Timed out waiting for Vite, proceeding anyway")


def stop_vite() -> None:
    if _vite_proc and _vite_proc.poll() is None:
        _vite_proc.terminate()
        log.info("Vite dev server stopped")


def build_frontend() -> None:
    src_frontend = Path(__file__).parent / "frontend"
    log.info("Building frontend")
    result = subprocess.run(["npm", "run", "build"], cwd=src_frontend, shell=True)
    if result.returncode != 0:
        log.error("Frontend build failed")
        sys.exit(1)
    log.info("Frontend build complete")


def _calc_window_size() -> tuple[int, int]:
    """根据屏幕分辨率计算最符合人体工程学的初始窗口尺寸。"""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        # 获取主屏物理像素（考虑 DPI 缩放）
        user32.SetProcessDPIAware()
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)
    except Exception:
        return 1200, 760

    # 黄金比例：宽 75%、高 78%，但不超过舒适上限
    w = min(int(sw * 0.75), 1500)
    h = min(int(sh * 0.78), 960)

    # 小屏（笔记本 1366×768 以下）适当收窄
    if sw <= 1366:
        w = min(int(sw * 0.88), 1200)
        h = min(int(sh * 0.85), 720)

    # 保证最小可用尺寸
    w = max(w, 900)
    h = max(h, 600)

    log.info("Screen %dx%d → window %dx%d", sw, sh, w, h)
    return w, h


def main():
    try:
        if _FROZEN:
            url = str(DIST_INDEX)
            log.info("Running in frozen mode, url=%s", url)
        elif _dev_mode:
            start_vite()
            url = DEV_URL
            log.info("Running in dev mode, url=%s", url)
        else:
            build_frontend()
            url = str(DIST_INDEX)
            log.info("Running in production mode, url=%s", url)

        win_w, win_h = _calc_window_size()
        api = API()
        webview.create_window(
            title="Chroma Walnut UI",
            url=url,
            js_api=api,
            width=win_w,
            height=win_h,
            min_size=(900, 600),
        )
        apply_window_icon()
        webview.start(debug=_dev_mode and not _FROZEN)
        log.info("Application exited normally")
    except Exception:
        log.critical("Fatal error in main()\n%s", traceback.format_exc())
        raise
    finally:
        if _dev_mode and not _FROZEN:
            stop_vite()


if __name__ == "__main__":
    main()
