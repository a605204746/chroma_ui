"""Generate and apply the walnut window icon (cross-platform).

图标在运行时按需生成到 ~/.chroma_walnut_ui/，路径传给
``webview.start(icon=...)``（见 backend/core/window.py → Application.run）。
打包脚本（scripts/build*.py）也复用这里的生成函数制作可执行文件图标。
"""
import struct
import sys
import zlib
from pathlib import Path

_ICON_DIR = Path.home() / ".chroma_walnut_ui"
ICO_PATH = _ICON_DIR / "walnut.ico"
ICNS_PATH = _ICON_DIR / "walnut.icns"
PNG_PATH = _ICON_DIR / "walnut.png"


def _make_walnut_png(size: int = 256) -> bytes:
    cx = cy = size // 2
    r = cx - 3

    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = (dx * dx + dy * dy) ** 0.5

            if dist > r:
                row += b'\x00\x00\x00\x00'
                continue

            # Edge anti-aliasing: maps dist in [r-2, r] → alpha [255, 0]
            alpha = 255 if dist <= r - 2 else max(0, int(255 * (r - dist) / 2))

            # Warm brown base — lighter top, darker bottom
            t = (dy + r) / (2 * r)
            pr = int(212 - 55 * t)
            pg = int(145 - 42 * t)
            pb = int(58 - 18 * t)

            seam_y = int(r * 0.08)
            seam_w = max(2, size // 46)
            ridge_w = max(2, size // 58)

            if abs(dy - seam_y) < seam_w:
                # Horizontal seam
                pr, pg, pb = int(pr * 0.50), int(pg * 0.50), int(pb * 0.50)
            elif abs(dx) < ridge_w:
                # Vertical center ridge
                pr, pg, pb = int(pr * 0.58), int(pg * 0.58), int(pb * 0.58)
            else:
                lw = max(1, size // 55)
                s = size / 64
                # Top-left wrinkle
                if -r * 0.65 < dx < -r * 0.08 and -r * 0.55 < dy < -r * 0.08:
                    line_val = dy - (-0.28 * dx - r * 0.15 * s)
                    if abs(line_val) < lw:
                        pr, pg, pb = int(pr * 0.58), int(pg * 0.58), int(pb * 0.58)
                # Top-right wrinkle
                elif r * 0.08 < dx < r * 0.65 and -r * 0.55 < dy < -r * 0.08:
                    line_val = dy - (0.28 * dx - r * 0.15 * s)
                    if abs(line_val) < lw:
                        pr, pg, pb = int(pr * 0.58), int(pg * 0.58), int(pb * 0.58)
                # Bottom-left wrinkle
                elif -r * 0.65 < dx < -r * 0.08 and r * 0.20 < dy < r * 0.65:
                    line_val = dy - (0.28 * dx + r * 0.50 * s)
                    if abs(line_val) < lw:
                        pr, pg, pb = int(pr * 0.58), int(pg * 0.58), int(pb * 0.58)
                # Bottom-right wrinkle
                elif r * 0.08 < dx < r * 0.65 and r * 0.20 < dy < r * 0.65:
                    line_val = dy - (-0.28 * dx + r * 0.50 * s)
                    if abs(line_val) < lw:
                        pr, pg, pb = int(pr * 0.58), int(pg * 0.58), int(pb * 0.58)

            # Highlight (top-left)
            h_dx, h_dy = dx + r * 0.24, dy + r * 0.30
            h_dist = (h_dx * h_dx + h_dy * h_dy) ** 0.5
            if h_dist < r * 0.27:
                blend = (1 - h_dist / (r * 0.27)) * 0.44
                pr = int(pr + (248 - pr) * blend)
                pg = int(pg + (210 - pg) * blend)
                pb = int(pb + (122 - pb) * blend)

            row += bytes([
                max(0, min(255, pr)),
                max(0, min(255, pg)),
                max(0, min(255, pb)),
                max(0, min(255, alpha)),
            ])
        rows.append(bytes(row))

    def chunk(name: bytes, data: bytes) -> bytes:
        c = name + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

    raw = b''.join(b'\x00' + row for row in rows)
    return (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(raw, 1))
        + chunk(b'IEND', b'')
    )


def _make_walnut_ico() -> bytes:
    """Wrap a 256×256 PNG in an ICO container (Windows Vista+ format)."""
    png = _make_walnut_png(256)
    header = struct.pack('<HHH', 0, 1, 1)   # reserved, type=ICO, count=1
    offset = 6 + 16
    entry = struct.pack('<BBBBHHII', 0, 0, 0, 0, 1, 32, len(png), offset)
    return header + entry + png


def _make_walnut_icns() -> bytes:
    """Wrap PNG images in an ICNS container (macOS format)."""
    def icns_entry(type_code: bytes, png_data: bytes) -> bytes:
        entry_len = 8 + len(png_data)
        return type_code + struct.pack('>I', entry_len) + png_data

    # ic07=128×128, ic08=256×256
    entries = (
        icns_entry(b'ic07', _make_walnut_png(128))
        + icns_entry(b'ic08', _make_walnut_png(256))
    )
    total_len = 8 + len(entries)
    return b'icns' + struct.pack('>I', total_len) + entries


def ensure_icon() -> Path:
    if not ICO_PATH.exists():
        ICO_PATH.parent.mkdir(parents=True, exist_ok=True)
        ICO_PATH.write_bytes(_make_walnut_ico())
    return ICO_PATH


def ensure_icon_icns() -> Path:
    if not ICNS_PATH.exists():
        ICNS_PATH.parent.mkdir(parents=True, exist_ok=True)
        ICNS_PATH.write_bytes(_make_walnut_icns())
    return ICNS_PATH


def ensure_icon_png() -> Path:
    if not PNG_PATH.exists():
        PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
        PNG_PATH.write_bytes(_make_walnut_png(256))
    return PNG_PATH


def app_icon_path() -> str:
    """当前平台的窗口图标路径（传给 pywebview 的 icon 参数）。"""
    if sys.platform == "win32":
        return str(ensure_icon())
    if sys.platform == "darwin":
        return str(ensure_icon_icns())
    return str(ensure_icon_png())
