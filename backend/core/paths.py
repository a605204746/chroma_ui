"""
路径解析：区分开发模式与 PyInstaller 打包模式。

  resource(rel)  — 打包进 bundle 的只读资源（frontend/dist、图标）
  userdata(rel)  — 可读写的用户文件（data/），始终在可执行文件旁边
"""
import os
import sys


def _bundle_base() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _exe_base() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def resource(relative: str) -> str:
    """打包进 bundle 的资源的绝对路径。"""
    return os.path.normpath(os.path.join(_bundle_base(), relative))


def userdata(relative: str) -> str:
    """可执行文件旁边的用户数据绝对路径（data/ 等）。"""
    return os.path.normpath(os.path.join(_exe_base(), relative))
