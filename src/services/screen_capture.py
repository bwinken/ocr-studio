"""Screen capture using mss."""

import io

import mss
from PIL import Image


class ScreenCaptureService:
    def capture_region(self, x: int, y: int, width: int, height: int) -> bytes:
        """Capture a specific rectangle. Returns PNG bytes."""
        with mss.mss() as sct:
            region = {"left": x, "top": y, "width": width, "height": height}
            screenshot = sct.grab(region)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()

    def capture_full_screen(self, monitor_index: int = 0) -> bytes:
        """Capture entire monitor. Returns PNG bytes."""
        with mss.mss() as sct:
            monitor = sct.monitors[monitor_index + 1]  # monitors[0] is virtual
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()

    def get_monitor_geometry(self, monitor_index: int = 0) -> dict:
        """Get monitor geometry: left, top, width, height."""
        with mss.mss() as sct:
            mon = sct.monitors[monitor_index + 1]
            return {"left": mon["left"], "top": mon["top"],
                    "width": mon["width"], "height": mon["height"]}
