"""First-time API setup page shown when no API key is configured."""

import httpx
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.constants import UI


class SetupPage(QWidget):
    """Shown on first launch to configure API key and base URL."""

    setup_complete = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Center container
        container = QWidget()
        container.setMaximumWidth(500)
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        # Title
        title = QLabel(UI["setup_title"])
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel(UI["setup_subtitle"])
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; color: #8181A5;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Base URL
        url_label = QLabel(UI["base_url"])
        url_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(url_label)

        self._base_url_edit = QLineEdit()
        self._base_url_edit.setPlaceholderText(UI["base_url_placeholder"])
        self._base_url_edit.setText(self._config.get_base_url())
        self._base_url_edit.setMinimumHeight(40)
        layout.addWidget(self._base_url_edit)

        # API Key
        key_label = QLabel(UI["api_key"])
        key_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(key_label)

        self._api_key_edit = QLineEdit()
        self._api_key_edit.setPlaceholderText(UI["api_key_placeholder"])
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_edit.setMinimumHeight(40)
        layout.addWidget(self._api_key_edit)

        layout.addSpacing(10)

        # Buttons
        btn_row = QHBoxLayout()

        self._test_btn = QPushButton(UI["test_connection"])
        self._test_btn.setProperty("secondary", True)
        self._test_btn.setMinimumHeight(44)
        self._test_btn.clicked.connect(self._test_connection)
        btn_row.addWidget(self._test_btn)

        self._save_btn = QPushButton(UI["save_and_start"])
        self._save_btn.setMinimumHeight(44)
        self._save_btn.clicked.connect(self._save_and_start)
        btn_row.addWidget(self._save_btn)

        layout.addLayout(btn_row)

        # Status
        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status)

        outer.addWidget(container)

    def _test_connection(self):
        api_key = self._api_key_edit.text().strip()
        base_url = self._base_url_edit.text().strip() or "https://api.openai.com/v1"

        if not api_key:
            self._status.setText(UI["no_api_key"])
            self._status.setStyleSheet("color: #D93025;")
            return

        self._test_btn.setEnabled(False)
        self._test_btn.setText("...")
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

            self._status.setText(UI["test_success"])
            self._status.setStyleSheet("color: #006F0C;")
        except Exception as e:
            self._status.setText(f"{UI['test_fail']}：{e}")
            self._status.setStyleSheet("color: #D93025;")
        finally:
            self._test_btn.setEnabled(True)
            self._test_btn.setText(UI["test_connection"])

    def _save_and_start(self):
        api_key = self._api_key_edit.text().strip()
        base_url = self._base_url_edit.text().strip() or "https://api.openai.com/v1"

        if not api_key:
            self._status.setText(UI["no_api_key"])
            self._status.setStyleSheet("color: #D93025;")
            return

        self._config.set("openai/api_key", api_key)
        self._config.set("openai/base_url", base_url)
        self.setup_complete.emit()
