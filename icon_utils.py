"""Generate and apply the walnut window icon (Windows)."""
import sys
import struct
import zlib
import threading
import time
from pathlib import Path

ICON_PATH = Path.home() / ".chroma_walnut_ui" / "walnut.ico"
_WINDOW_TITLE = "Chroma Walnut UI"


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


def ensure_icon() -> Path:
    if not ICON_PATH.exists():
        ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
        ICON_PATH.write_bytes(_make_walnut_ico())
    return ICON_PATH


def _set_win32_icon(icon_path: Path, max_wait: float = 6.0, interval: float = 0.3):
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        u32 = ctypes.windll.user32
        LR_LOADFROMFILE = 0x10
        IMAGE_ICON = 1
        WM_SETICON = 0x80

        hIcon = u32.LoadImageW(None, str(icon_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
        if not hIcon:
            return

        elapsed = 0.0
        while elapsed < max_wait:
            hwnd = u32.FindWindowW(None, _WINDOW_TITLE)
            if hwnd:
                u32.SendMessageW(hwnd, WM_SETICON, 0, hIcon)  # ICON_SMALL
                u32.SendMessageW(hwnd, WM_SETICON, 1, hIcon)  # ICON_BIG
                return
            time.sleep(interval)
            elapsed += interval
    except Exception as e:
        print(f"[icon] {e}")


def apply_window_icon():
    """Generate the ICO (once) and spawn a thread to stamp it onto the window."""
    ico = ensure_icon()
    threading.Thread(target=_set_win32_icon, args=(ico,), daemon=True).start()
