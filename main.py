import subprocess
import sys
from pathlib import Path

import webview
from api import API
from icon_utils import apply_window_icon

DEV_URL = "http://localhost:5173"
FRONTEND_DIR = Path(__file__).parent / "frontend"
DIST_DIR = FRONTEND_DIR / "dist" / "index.html"


def build_frontend():
    print("正在构建前端...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND_DIR,
        shell=True,
    )
    if result.returncode != 0:
        print("前端构建失败，请检查错误信息。")
        sys.exit(1)
    print("前端构建完成。")


def main():
    dev_mode = "--dev" in sys.argv
    if not dev_mode:
        build_frontend()
    url = DEV_URL if dev_mode else str(DIST_DIR)

    api = API()
    window = webview.create_window(
        title="Chroma Walnut UI",
        url=url,
        js_api=api,
        width=1280,
        height=800,
        min_size=(900, 600),
    )
    apply_window_icon()
    webview.start(debug=dev_mode)


if __name__ == "__main__":
    main()
