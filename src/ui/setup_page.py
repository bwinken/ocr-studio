"""First-time API setup page — guided onboarding."""

import httpx
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.constants import UI


class SetupPage(QWidget):
    setup_complete = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container = QWidget()
        container.setMaximumWidth(480)
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        # Step icon
        icon = QLabel("\U0001F511")  # 🔑
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 40px; border: none;")
        layout.addWidget(icon)

        # Title
        title = QLabel("設定 API 連線")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 400; color: #1F1F1F;")
        layout.addWidget(title)

        subtitle = QLabel("OCR Studio 需要 OpenAI 相容的 API 來進行文字辨識與翻譯")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 13px; color: #8181A5;")
        layout.addWidget(subtitle)

        layout.addSpacing(12)

        # Base URL
        url_label = QLabel("API Base URL")
        url_label.setStyleSheet("font-size: 12px; font-weight: 500; color: #8181A5;")
        layout.addWidget(url_label)

        self._base_url_edit = QLineEdit()
        self._base_url_edit.setPlaceholderText("https://api.openai.com/v1")
        self._base_url_edit.setText(self._config.get_base_url())
        self._base_url_edit.setMinimumHeight(40)
        layout.addWidget(self._base_url_edit)

        # API Key
        key_label = QLabel("API Key")
        key_label.setStyleSheet("font-size: 12px; font-weight: 500; color: #8181A5;")
        layout.addWidget(key_label)

        self._api_key_edit = QLineEdit()
        self._api_key_edit.setPlaceholderText("sk-...")
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_edit.setMinimumHeight(40)
        layout.addWidget(self._api_key_edit)

        # Hint
        hint = QLabel(
            "\U0001F4A1 支援 OpenAI、Azure、vLLM、Ollama 等相容 API"
        )
        hint.setStyleSheet("font-size: 11px; color: #ADADC0;")
        layout.addWidget(hint)

        layout.addSpacing(8)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._test_btn = QPushButton("\u26A1 " + UI["test_connection"])
        self._test_btn.setProperty("secondary", True)
        self._test_btn.setMinimumHeight(42)
        self._test_btn.clicked.connect(self._test_connection)
        btn_row.addWidget(self._test_btn)

        self._save_btn = QPushButton(UI["save_and_start"] + " \u2192")
        self._save_btn.setMinimumHeight(42)
        self._save_btn.clicked.connect(self._save_and_start)
        btn_row.addWidget(self._save_btn)

        layout.addLayout(btn_row)

        # Status
        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        outer.addWidget(container)

    def _test_connection(self):
        api_key = self._api_key_edit.text().strip()
        base_url = self._base_url_edit.text().strip() or "https://api.openai.com/v1"

        if not api_key:
            self._status.setText("\u26A0 請先輸入 API Key")
            self._status.setStyleSheet("color: #D93025;")
            return

        self._test_btn.setEnabled(False)
        self._test_btn.setText("\u23F3 測試中...")
        self._status.setText("")

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Say OK"}],
                "max_completion_tokens": 5,
            }
            with httpx.Client(timeout=15) as client:
                resp = client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
                if resp.status_code >= 400:
                    try:
                        body = resp.json()
                        err_msg = body.get("error", {}).get("message", resp.text)
                    except Exception:
                        err_msg = resp.text
                    raise RuntimeError(f"{resp.status_code}: {err_msg}")

            self._status.setText("\u2705 連線成功！")
            self._status.setStyleSheet("color: #006F0C;")
        except Exception as e:
            self._status.setText(f"\u274C 連線失敗：{e}")
            self._status.setStyleSheet("color: #D93025;")
        finally:
            self._test_btn.setEnabled(True)
            self._test_btn.setText("\u26A1 " + UI["test_connection"])

    def _save_and_start(self):
        api_key = self._api_key_edit.text().strip()
        base_url = self._base_url_edit.text().strip() or "https://api.openai.com/v1"

        if not api_key:
            self._status.setText("\u26A0 請先輸入 API Key")
            self._status.setStyleSheet("color: #D93025;")
            return

        self._config.set("openai/api_key", api_key)
        self._config.set("openai/base_url", base_url)
        self.setup_complete.emit()
