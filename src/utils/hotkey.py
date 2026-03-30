"""Global hotkey registration using Windows RegisterHotKey API."""

import ctypes
import ctypes.wintypes

from PySide6.QtCore import QThread, Signal

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312


class GlobalHotkey(QThread):
    """Registers a system-wide hotkey. Emits triggered() when pressed."""

    triggered = Signal()
    HOTKEY_ID = 1

    def __init__(self, key_string: str = "Ctrl+Shift+O"):
        super().__init__()
        self._modifiers, self._vk = self._parse_hotkey(key_string)
        self._running = True

    @staticmethod
    def _parse_hotkey(key_string: str) -> tuple[int, int]:
        """Parse 'Ctrl+Shift+O' into (modifier_flags, virtual_key_code)."""
        parts = [p.strip().lower() for p in key_string.split("+")]
        mods = 0
        vk = 0
        for part in parts:
            if part == "ctrl":
                mods |= MOD_CONTROL
            elif part == "shift":
                mods |= MOD_SHIFT
            elif part == "alt":
                mods |= MOD_ALT
            elif part == "win":
                mods |= MOD_WIN
            elif len(part) == 1:
                vk = ord(part.upper())
            else:
                # Handle special keys
                special = {
                    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
                    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
                    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
                    "space": 0x20, "enter": 0x0D, "tab": 0x09,
                    "escape": 0x1B, "esc": 0x1B,
                    "printscreen": 0x2C, "prtsc": 0x2C,
                }
                vk = special.get(part, 0)
        return mods, vk

    def run(self):
        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, self.HOTKEY_ID, self._modifiers, self._vk):
            return

        msg = ctypes.wintypes.MSG()
        while self._running:
            # Use GetMessage with a timeout approach via PeekMessage
            ret = user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1)
            if ret:
                if msg.message == WM_HOTKEY and msg.wParam == self.HOTKEY_ID:
                    self.triggered.emit()
            else:
                self.msleep(50)

        user32.UnregisterHotKey(None, self.HOTKEY_ID)

    def stop(self):
        self._running = False
        self.wait(2000)

    def update_hotkey(self, key_string: str):
        """Re-register with new key combo."""
        self.stop()
        self._modifiers, self._vk = self._parse_hotkey(key_string)
        self._running = True
        self.start()
