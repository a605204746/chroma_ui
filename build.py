#!/usr/bin/env python3
"""
Chroma Walnut UI — 跨平台一键打包脚本

用法:
    uv run python build.py           # 正式包（无控制台）
    uv run python build.py --debug   # 调试包（保留控制台，可看错误）

支持平台:
    Windows  → dist/ChromaWalnutUI/ChromaWalnutUI.exe（onedir）
    macOS    → dist/ChromaWalnutUI.app（app bundle）
    Linux    → dist/ChromaWalnutUI/ChromaWalnutUI（onedir）
"""
import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
FRONTEND_DIR = ROOT / "frontend"
APP_NAME = "ChromaWalnutUI"
PYTHON = sys.executable
DEBUG_MODE = "--debug" in sys.argv
PLATFORM = sys.platform  # 'win32' | 'darwin' | 'linux'

# 平台对应图标路径
_ICON_PATHS = {
    "win32":  ROOT / "_build_icon.ico",
    "darwin": ROOT / "_build_icon.icns",
    "linux":  ROOT / "_build_icon.png",
}
ICON_FILE = _ICON_PATHS.get(PLATFORM, ROOT / "_build_icon.png")


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
    use_shell = isinstance(args, str)
    result = subprocess.run(args, cwd=cwd, shell=use_shell)
    if result.returncode != 0:
        _fail(f"命令失败: {args!r}")


# ── 步骤 1: 环境检查 ──────────────────────────────────────────────────────────

def check_env():
    _step("检查环境")

    if sys.version_info < (3, 12):
        _fail(f"需要 Python 3.12+，当前为 {sys.version}")
    _ok(f"Python {sys.version.split()[0]}  [{PLATFORM}]")

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
        if shutil.which("uv"):
            _run("uv add --dev pyinstaller")
        else:
            _run([PYTHON, "-m", "pip", "install", "pyinstaller"])
        r = subprocess.run(
            [PYTHON, "-m", "PyInstaller", "--version"],
            capture_output=True, text=True,
        )
    _ok(f"PyInstaller {r.stdout.strip()}")

    if PLATFORM == "darwin":
        _check_macos_deps()
    elif PLATFORM == "linux":
        _check_linux_deps()


def _check_macos_deps():
    """检查 macOS 必需的 pyobjc 包。"""
    import importlib
    missing = []
    for pkg in ("Cocoa", "WebKit"):
        try:
            importlib.import_module(pkg)
        except ModuleNotFoundError:
            missing.append(f"pyobjc-framework-{pkg}")
    if missing:
        _step(f"安装 macOS 依赖: {' '.join(missing)}")
        _run([PYTHON, "-m", "pip", "install"] + missing)
    _ok("macOS pyobjc 依赖就绪")


def _check_linux_deps():
    """提示 Linux 系统依赖（无法自动安装）。"""
    r = subprocess.run(
        ["python3", "-c", "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk"],
        capture_output=True,
    )
    if r.returncode != 0:
        print()
        print("  [!] Linux 需要预先安装以下系统包：")
        print("      sudo apt-get install -y \\")
        print("        python3-gi python3-gi-cairo gir1.2-gtk-3.0 \\")
        print("        gir1.2-webkit2-4.1 libgirepository1.0-dev gcc \\")
        print("        libcairo2-dev pkg-config python3-dev")
        print()
        _fail("缺少 GTK/WebKitGTK 系统依赖，请安装后重试")
    _ok("GTK / WebKitGTK 就绪")


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
    _step(f"生成应用图标 ({ICON_FILE.name})")
    sys.path.insert(0, str(ROOT))
    from icon_utils import _make_walnut_ico, _make_walnut_icns, _make_walnut_png

    if PLATFORM == "win32":
        ICON_FILE.write_bytes(_make_walnut_ico())
    elif PLATFORM == "darwin":
        ICON_FILE.write_bytes(_make_walnut_icns())
    else:
        # Linux: 使用 PNG
        ICON_FILE.write_bytes(_make_walnut_png(256))

    _ok(f"图标生成 → {ICON_FILE.name}")


# ── 步骤 4: PyInstaller 打包 ──────────────────────────────────────────────────

def _force_remove_dist():
    for target in [ROOT / "dist" / APP_NAME, ROOT / "dist" / f"{APP_NAME}.app"]:
        if not target.exists():
            continue
        try:
            shutil.rmtree(target)
            _ok(f"已清理旧目录: {target.relative_to(ROOT)}")
        except PermissionError:
            _fail(
                f"无法删除 {target}，该目录被占用。\n"
                "   请先关闭正在运行的应用，再重新打包。"
            )


def _add_data_arg(src: str, dst: str) -> str:
    sep = ";" if PLATFORM == "win32" else ":"
    return f"{src}{sep}{dst}"


def package():
    mode_label = "调试模式（含控制台）" if DEBUG_MODE else "正式模式（无控制台）"
    _step(f"PyInstaller 打包 — {mode_label} [{PLATFORM}]")

    _force_remove_dist()

    frontend_dist = str(FRONTEND_DIR / "dist")

    args = [
        PYTHON, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--add-data", _add_data_arg(frontend_dist, "frontend/dist"),

        # ChromaDB / ONNX 全量收集
        "--collect-all", "chromadb",
        "--collect-all", "onnxruntime",

        # PyWebView 公共收集
        "--collect-all", "webview",

        "--noconfirm",
        "--clean",
    ]

    if ICON_FILE.exists():
        args += ["--icon", str(ICON_FILE)]

    # 平台专属参数
    if PLATFORM == "win32":
        args += [
            "--hidden-import", "webview.platforms.winforms",
            "--hidden-import", "webview.platforms.edgechromium",
            "--hidden-import", "clr",
            "--collect-all", "pythonnet",
        ]
    elif PLATFORM == "darwin":
        args += [
            "--hidden-import", "webview.platforms.cocoa",
            "--osx-bundle-identifier", "com.chromawalnutui.app",
        ]
    else:  # linux
        args += [
            "--hidden-import", "webview.platforms.gtk",
            "--hidden-import", "gi",
            "--collect-all", "gi",
        ]

    # 窗口模式
    args.append("--console" if DEBUG_MODE else "--windowed")

    args.append(str(ROOT / "main.py"))

    _run(args, cwd=ROOT)

    # 验证输出
    if PLATFORM == "darwin":
        exe = ROOT / "dist" / f"{APP_NAME}.app" / "Contents" / "MacOS" / APP_NAME
    elif PLATFORM == "win32":
        exe = ROOT / "dist" / APP_NAME / f"{APP_NAME}.exe"
    else:
        exe = ROOT / "dist" / APP_NAME / APP_NAME

    if not exe.exists():
        _fail(f"打包结束但未找到可执行文件: {exe}")

    out_dir = exe.parent if PLATFORM != "darwin" else (ROOT / "dist" / f"{APP_NAME}.app")
    _ok(f"可执行文件 → {exe.relative_to(ROOT)}")
    _ok(f"分发目录大小: {_dir_size(out_dir)}")


# ── 步骤 5: 打包分发文件 ──────────────────────────────────────────────────────

def archive():
    _step("创建分发压缩包")
    dist_dir = ROOT / "dist"

    if PLATFORM == "win32":
        out = dist_dir / f"{APP_NAME}-Windows.zip"
        _run(["powershell", "-Command",
              f"Compress-Archive -Path '{dist_dir / APP_NAME}\\*' -DestinationPath '{out}' -Force"])
        _ok(f"Windows 压缩包 → dist/{out.name}")
    elif PLATFORM == "darwin":
        out = dist_dir / f"{APP_NAME}-macOS.dmg"
        result = subprocess.run([
            "hdiutil", "create",
            "-volname", "ChromaWalnutUI",
            "-srcfolder", str(dist_dir / f"{APP_NAME}.app"),
            "-ov", "-format", "UDZO",
            str(out),
        ])
        if result.returncode == 0:
            _ok(f"macOS DMG → dist/{out.name}")
        else:
            # hdiutil 失败时退回 zip
            out = dist_dir / f"{APP_NAME}-macOS.zip"
            shutil.make_archive(
                str(dist_dir / f"{APP_NAME}-macOS"),
                "zip",
                str(dist_dir),
                f"{APP_NAME}.app",
            )
            _ok(f"macOS 压缩包（fallback zip）→ dist/{out.name}")
    else:  # linux
        out = dist_dir / f"{APP_NAME}-Linux.tar.gz"
        import tarfile
        with tarfile.open(out, "w:gz") as tar:
            tar.add(dist_dir / APP_NAME, arcname=APP_NAME)
        _ok(f"Linux 压缩包 → dist/{out.name}")


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
    platform_label = {"win32": "Windows", "darwin": "macOS"}.get(PLATFORM, "Linux")
    _banner(f"Chroma Walnut UI — {platform_label} 一键打包")
    if DEBUG_MODE:
        print("  [调试模式] 打包结果含控制台窗口，可直接看到 Python 错误信息")

    try:
        check_env()
        build_frontend()
        generate_icon()
        package()
        archive()
    except SystemExit:
        raise
    except Exception as e:
        _fail(f"意外错误: {e}")
    finally:
        cleanup()

    _banner("打包完成")
    dist_dir = ROOT / "dist"
    if PLATFORM == "win32":
        print(f"  分发文件: {dist_dir / f'{APP_NAME}-Windows.zip'}")
        print(f"  或直接使用目录: {dist_dir / APP_NAME}/")
        print()
        print("  运行要求: Windows 10 1803+ / Windows 11（已内置 WebView2）")
    elif PLATFORM == "darwin":
        print(f"  分发文件: {dist_dir / f'{APP_NAME}-macOS.dmg'}")
        print(f"  或直接使用: {dist_dir / f'{APP_NAME}.app'}")
        print()
        print("  运行要求: macOS 10.15 Catalina+")
        print("  注意: 分发前建议使用 codesign 对 .app 进行签名")
    else:
        print(f"  分发文件: {dist_dir / f'{APP_NAME}-Linux.tar.gz'}")
        print()
        print("  运行要求: Ubuntu 20.04+ / Debian 11+，需安装 WebKitGTK")
        print("  apt: libwebkit2gtk-4.1-0 libgtk-3-0")
    print()


if __name__ == "__main__":
    main()
