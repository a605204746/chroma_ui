import subprocess
import sys
import logging
import traceback
from pathlib import Path

# ── 冻结模式（PyInstaller）适配 ───────────────────────────────────────────────
_FROZEN = getattr(sys, 'frozen', False)
# 打包后资源在 sys._MEIPASS，源码运行时是当前脚本目录
_BASE_DIR = Path(sys._MEIPASS) if _FROZEN else Path(__file__).parent

# 打包后把错误写到日志文件（--windowed 模式下控制台不可见）
if _FROZEN:
    _log_path = Path.home() / '.chroma_walnut_ui' / 'error.log'
    _log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(_log_path),
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(message)s',
    )
    def _excepthook(exc_type, exc_val, exc_tb):
        logging.error('Uncaught exception', exc_info=(exc_type, exc_val, exc_tb))
    sys.excepthook = _excepthook

import webview
from api import API
from icon_utils import apply_window_icon

DEV_URL = "http://localhost:5173"
FRONTEND_DIR = _BASE_DIR / "frontend"
DIST_INDEX = FRONTEND_DIR / "dist" / "index.html"


def build_frontend():
    src_frontend = Path(__file__).parent / "frontend"
    print("正在构建前端...")
    result = subprocess.run(["npm", "run", "build"], cwd=src_frontend, shell=True)
    if result.returncode != 0:
        print("前端构建失败，请检查错误信息。")
        sys.exit(1)
    print("前端构建完成。")


def main():
    try:
        dev_mode = "--dev" in sys.argv

        if _FROZEN:
            url = str(DIST_INDEX)
        elif dev_mode:
            url = DEV_URL
        else:
            build_frontend()
            url = str(DIST_INDEX)

        logging.info("Starting Chroma Walnut UI, url=%s", url)

        api = API()
        webview.create_window(
            title="Chroma Walnut UI",
            url=url,
            js_api=api,
            width=1280,
            height=800,
            min_size=(900, 600),
        )
        apply_window_icon()
        webview.start(debug=dev_mode and not _FROZEN)
    except Exception:
        logging.error("Fatal error in main()\n%s", traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
