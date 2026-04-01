"""Settings page — simplified, save button top-right."""

import httpx
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.constants import TARGET_LANGUAGES, UI


class SettingsTab(QWidget):
    settings_changed = Signal()

    def __init__(self, config):
        super().__init__()
        self._config = config
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Top bar: title + save button ──
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(24, 14, 24, 10)

        title = QLabel("設定")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        top_bar.addWidget(title)
        top_bar.addStretch()

        save_btn = QPushButton("\U0001F4BE 儲存設定")
        save_btn.setToolTip("儲存所有設定並套用")
        save_btn.clicked.connect(self._save_settings)
        top_bar.addWidget(save_btn)

        outer.addLayout(top_bar)

        # ── Scrollable content ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 8, 24, 24)

        # ── API 連線 ──
        api_group = QGroupBox("API 連線")
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(10)

        self._base_url_edit = QLineEdit()
        self._base_url_edit.setPlaceholderText("https://api.openai.com/v1")
        self._base_url_edit.setToolTip("OpenAI 相容 API 的 Base URL")
        api_layout.addRow("Base URL:", self._base_url_edit)

        key_row = QHBoxLayout()
        self._api_key_edit = QLineEdit()
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_edit.setPlaceholderText("sk-...")
        key_row.addWidget(self._api_key_edit, 1)
        self._test_btn = QPushButton("測試")
        self._test_btn.setProperty("secondary", True)
        self._test_btn.setFixedWidth(70)
        self._test_btn.clicked.connect(self._test_api_key)
        key_row.addWidget(self._test_btn)
        key_widget = QWidget()
        key_widget.setLayout(key_row)
        api_layout.addRow("API Key:", key_widget)

        layout.addWidget(api_group)

        # ── 模型 ──
        model_group = QGroupBox("模型設定")
        model_layout = QFormLayout(model_group)
        model_layout.setSpacing(10)

        self._ocr_model_combo = QComboBox()
        self._ocr_model_combo.setEditable(True)
        self._ocr_model_combo.setToolTip(
            "模型名包含 paddle 會自動切換 PaddleOCR 模式"
        )
        self._ocr_model_combo.addItems([
            "gpt-4o", "gpt-4o-mini", "gpt-5.4-nano",
            "PaddleOCR-VL-1.5-0.9B",
        ])
        model_layout.addRow("OCR 模型:", self._ocr_model_combo)

        self._translate_model_combo = QComboBox()
        self._translate_model_combo.setEditable(True)
        self._translate_model_combo.setToolTip("翻譯使用的模型")
        self._translate_model_combo.addItems([
            "gpt-4o", "gpt-4o-mini", "gpt-5.4-nano",
        ])
        model_layout.addRow("翻譯模型:", self._translate_model_combo)

        self._language_combo = QComboBox()
        self._language_combo.setToolTip("預設翻譯目標語言")
        self._language_combo.addItems(TARGET_LANGUAGES)
        model_layout.addRow("預設語言:", self._language_combo)

        layout.addWidget(model_group)

        # ── OCR 端點（進階） ──
        ocr_group = QGroupBox("OCR 獨立端點（選填）")
        ocr_layout = QFormLayout(ocr_group)
        ocr_layout.setSpacing(10)

        self._ocr_base_url_edit = QLineEdit()
        self._ocr_base_url_edit.setPlaceholderText("留空 = 使用上方 Base URL")
        self._ocr_base_url_edit.setToolTip(
            "OCR 模型部署在不同伺服器時填寫\n"
            "例如：http://localhost:8000/v1"
        )
        ocr_layout.addRow("OCR Base URL:", self._ocr_base_url_edit)

        self._ocr_api_key_edit = QLineEdit()
        self._ocr_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._ocr_api_key_edit.setPlaceholderText("留空 = 使用上方 API Key")
        ocr_layout.addRow("OCR API Key:", self._ocr_api_key_edit)

        layout.addWidget(ocr_group)

        # ── 快捷鍵 ──
        hotkey_group = QGroupBox("快捷鍵")
        hotkey_layout = QFormLayout(hotkey_group)
        hotkey_layout.setSpacing(10)

        self._hotkey_edit = QLineEdit()
        self._hotkey_edit.setPlaceholderText("Ctrl+Shift+O")
        self._hotkey_edit.setToolTip("全域截圖快捷鍵")
        hotkey_layout.addRow("截圖快捷鍵:", self._hotkey_edit)

        layout.addWidget(hotkey_group)

        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _load_settings(self):
        c = self._config
        self._api_key_edit.setText(c.get_api_key())
        self._base_url_edit.setText(c.get_base_url())
        self._ocr_model_combo.setCurrentText(str(c.get("openai/ocr_model", "gpt-4o")))
        self._translate_model_combo.setCurrentText(str(c.get("openai/translate_model", "gpt-4o")))
        self._language_combo.setCurrentText(str(c.get("general/target_language", "English")))
        self._hotkey_edit.setText(c.get_hotkey())
        self._ocr_base_url_edit.setText(str(c.get("ocr/base_url", "")))
        self._ocr_api_key_edit.setText(str(c.get("ocr/api_key", "")))

    def _save_settings(self):
        c = self._config
        c.set("openai/api_key", self._api_key_edit.text().strip())
        c.set("openai/base_url", self._base_url_edit.text().strip() or "https://api.openai.com/v1")
        c.set("openai/ocr_model", self._ocr_model_combo.currentText())
        c.set("openai/translate_model", self._translate_model_combo.currentText())
        c.set("general/target_language", self._language_combo.currentText())
        c.set("general/hotkey", self._hotkey_edit.text().strip())
        c.set("ocr/base_url", self._ocr_base_url_edit.text().strip())
        c.set("ocr/api_key", self._ocr_api_key_edit.text().strip())
        self.settings_changed.emit()
        QMessageBox.information(self, "設定", "設定已儲存")

    def _test_api_key(self):
        api_key = self._api_key_edit.text().strip()
        base_url = self._base_url_edit.text().strip() or "https://api.openai.com/v1"
        if not api_key:
            QMessageBox.warning(self, "測試", "請先輸入 API Key")
            return

        self._test_btn.setEnabled(False)
        self._test_btn.setText("...")
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self._ocr_model_combo.currentText(),
                "messages": [{"role": "user", "content": "Say OK"}],
                "max_tokens": 5,
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
            QMessageBox.information(self, "測試", "連線成功！")
        except Exception as e:
            QMessageBox.critical(self, "連線失敗", str(e))
        finally:
            self._test_btn.setEnabled(True)
            self._test_btn.setText("測試")
