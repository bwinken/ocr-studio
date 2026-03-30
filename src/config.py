from PySide6.QtCore import QSettings

from src.constants import DEFAULT_HOTKEY


class ConfigManager:
    """Wraps QSettings. Stores to %APPDATA%/OCRStudio/settings.ini."""

    DEFAULTS = {
        "openai/api_key": "",
        "openai/base_url": "https://api.openai.com/v1",
        "openai/ocr_model": "gpt-4o",
        "openai/translate_model": "gpt-4o",
        "openai/max_tokens": 4096,
        "openai/temperature_ocr": 0.1,
        "openai/temperature_translate": 0.3,
        # Separate OCR endpoint (empty = use same as base)
        "ocr/base_url": "",
        "ocr/api_key": "",
        "ocr/structured_output": True,
        "general/target_language": "English",
        "general/hotkey": DEFAULT_HOTKEY,
        "general/start_minimized": False,
        "general/start_with_windows": False,
        "general/pdf_render_scale": 2.0,
        "capture/auto_translate": False,
        "capture/copy_to_clipboard": True,
        "batch/overlay_mode": "visible",
        "batch/export_source": "translated",
    }

    def __init__(self):
        self._settings = QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "OCRStudio",
            "settings",
        )

    def get(self, key: str, default=None):
        val = self._settings.value(key)
        if val is not None:
            return val
        if default is not None:
            return default
        return self.DEFAULTS.get(key)

    def set(self, key: str, value):
        self._settings.setValue(key, value)
        self._settings.sync()

    def get_api_key(self) -> str:
        return str(self.get("openai/api_key", ""))

    def get_base_url(self) -> str:
        return str(self.get("openai/base_url", "https://api.openai.com/v1"))

    def get_hotkey(self) -> str:
        return str(self.get("general/hotkey", DEFAULT_HOTKEY))
