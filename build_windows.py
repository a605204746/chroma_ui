#!/usr/bin/env python3
"""
Chroma Walnut UI — Windows 一键打包脚本

用法:
    uv run python build_windows.py
    python build_windows.py

输出:
    dist/ChromaWalnutUI/ChromaWalnutUI.exe  （及其依赖文件）
    将整个 dist/ChromaWalnutUI/ 目录分发给用户即可
"""
import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
FRONTEND_DIR = ROOT / "frontend"
APP_NAME = "ChromaWalnutUI"
ICON_FILE = ROOT / "_build_icon.ico"   # 构建时临时生成，完成后删除
PYTHON = sys.executable


# ── 输出工具 ──────────────────────────────────────────────────────────────────

def _banner(msg: str):
    bar = "─" * 56
    print(f"\n{bar}\n  {msg}\n{bar}")

def _step(msg: str):
    print(f"\n▶  {msg}")

def _ok(msg: str):
    print(f"   ✓  {msg}")

def _fail(msg: str):
    print(f"\n   ✗  {msg}\n")
    sys.exit(1)

def _run(args, cwd=None):
    """运行命令；字符串用 shell=True（npm.cmd），列表用 shell=False（Python 可执行文件）。"""
    use_shell = isinstance(args, str)
    result = subprocess.run(args, cwd=cwd, shell=use_shell)
    if result.returncode != 0:
        _fail(f"命令失败: {args!r}")


# ── 步骤 1: 环境检查 ──────────────────────────────────────────────────────────

def check_env():
    _step("检查环境")

    if sys.platform != "win32":
        _fail("此脚本仅支持 Windows")

    if sys.version_info < (3, 12):
        _fail(f"需要 Python 3.12+，当前为 {sys.version}")
    _ok(f"Python {sys.version.split()[0]}")

    for tool in ("node", "npm"):
        if shutil.which(tool) is None:
            _fail(f"未找到 '{tool}'，请先安装 Node.js：https://nodejs.org")
    _ok("Node.js / npm")

    r = subprocess.run(
        [PYTHON, "-m", "PyInstaller", "--version"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        _step("PyInstaller 未安装，正在安装…")
        # uv 环境没有 pip，通过 uv add 安装到项目 venv
        if shutil.which("uv"):
            _run("uv add --dev pyinstaller")
        else:
            _run([PYTHON, "-m", "ensurepip", "--upgrade"])
            _run([PYTHON, "-m", "pip", "install", "pyinstaller"])
        r = subprocess.run(
            [PYTHON, "-m", "PyInstaller", "--version"],
            capture_output=True, text=True,
        )
    _ok(f"PyInstaller {r.stdout.strip()}")


# ── 步骤 2: 构建前端 ──────────────────────────────────────────────────────────

def build_frontend():
    _step("构建前端 (npm install + npm run build)")
    _run("npm install", cwd=FRONTEND_DIR)
    _run("npm run build", cwd=FRONTEND_DIR)
    dist = FRONTEND_DIR / "dist"
    if not dist.exists():
        _fail("前端构建完成但未找到 dist/ 目录，请检查 Vite 配置")
    _ok(f"前端构建完成 → frontend/dist/ ({_dir_size(dist)})")


def _dir_size(path: Path) -> str:
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return f"{total / 1024 / 1024:.1f} MB"


# ── 步骤 3: 生成应用图标 ──────────────────────────────────────────────────────

def generate_icon():
    _step("生成应用图标 (walnut.ico)")
    sys.path.insert(0, str(ROOT))
    from icon_utils import _make_walnut_ico
    ICON_FILE.write_bytes(_make_walnut_ico())
    _ok(f"图标生成 → {ICON_FILE.name}")


# ── 步骤 4: PyInstaller 打包 ──────────────────────────────────────────────────

def package():
    _step("PyInstaller 打包 (onedir 模式)")

    frontend_dist = str(FRONTEND_DIR / "dist")

    args = [
        PYTHON, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--windowed",                                       # 无控制台窗口
        "--icon", str(ICON_FILE),
        "--add-data", f"{frontend_dist};frontend/dist",     # 打包前端资源
        "--hidden-import", "webview.platforms.winforms",    # PyWebView Windows 后端
        "--hidden-import", "webview.platforms.edgechromium",
        "--collect-all", "chromadb",                        # ChromaDB 全量收集
        "--collect-all", "onnxruntime",                     # ONNX Runtime（chromadb 依赖）
        "--noconfirm",
        "--clean",
        str(ROOT / "main.py"),
    ]

    _run(args, cwd=ROOT)

    exe = ROOT / "dist" / APP_NAME / f"{APP_NAME}.exe"
    if not exe.exists():
        _fail(f"打包结束但未找到可执行文件: {exe}")
    _ok(f"可执行文件 → dist/{APP_NAME}/{APP_NAME}.exe")
    dist_dir = exe.parent
    _ok(f"分发目录大小: {_dir_size(dist_dir)}")


# ── 清理临时文件 ──────────────────────────────────────────────────────────────

def cleanup():
    ICON_FILE.unlink(missing_ok=True)
    spec_file = ROOT / f"{APP_NAME}.spec"
    if spec_file.exists():
        spec_file.unlink()
    build_dir = ROOT / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)


# ── 主入口 ────────────────────────────────────────────────────────────────────

def main():
    _banner("Chroma Walnut UI — Windows 一键打包")

    try:
        check_env()
        build_frontend()
        generate_icon()
        package()
    except SystemExit:
        raise
    except Exception as e:
        _fail(f"意外错误: {e}")
    finally:
        cleanup()

    exe = ROOT / "dist" / APP_NAME / f"{APP_NAME}.exe"
    _banner("打包完成")
    print(f"  可执行文件: {exe}")
    print(f"  分发目录:   {exe.parent}")
    print()
    print("  注意：将整个 dist/ChromaWalnutUI/ 文件夹分发给用户，")
    print("        不要只分发 .exe 单文件，它依赖同目录下的其他文件。")
    print()
    print("  运行要求：用户 Windows 系统需已安装 Microsoft Edge（WebView2）。")
    print("            Windows 10 1803+ / Windows 11 默认已内置。")
    print()


if __name__ == "__main__":
    main()
