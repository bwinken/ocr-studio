import httpx
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
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
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # OpenAI API
        api_group = QGroupBox(UI["settings_api"])
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(12)

        self._api_key_edit = QLineEdit()
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_edit.setPlaceholderText("sk-...")

        key_row = QHBoxLayout()
        key_row.addWidget(self._api_key_edit, 1)
        self._test_btn = QPushButton(UI["test"])
        self._test_btn.setFixedWidth(80)
        self._test_btn.clicked.connect(self._test_api_key)
        key_row.addWidget(self._test_btn)

        api_key_widget = QWidget()
        api_key_widget.setLayout(key_row)
        api_layout.addRow(UI["api_key"] + ":", api_key_widget)

        self._base_url_edit = QLineEdit()
        self._base_url_edit.setPlaceholderText("https://api.openai.com/v1")
        api_layout.addRow(UI["base_url"] + ":", self._base_url_edit)

        self._ocr_model_combo = QComboBox()
        self._ocr_model_combo.setEditable(True)
        self._ocr_model_combo.setToolTip(
            "OCR 文字辨識使用的模型\n"
            "模型名包含 paddle 會自動切換 PaddleOCR 模式\n"
            "例如：PaddleOCR-VL-1.5-0.9B"
        )
        self._ocr_model_combo.addItems([
            "gpt-4o", "gpt-4o-mini", "gpt-5.4-nano",
            "PaddleOCR-VL-1.5-0.9B",
        ])
        api_layout.addRow(UI["ocr_model"] + ":", self._ocr_model_combo)

        self._translate_model_combo = QComboBox()
        self._translate_model_combo.setEditable(True)
        self._translate_model_combo.setToolTip("翻譯使用的模型，建議使用較大的語言模型")
        self._translate_model_combo.addItems([
            "gpt-4o", "gpt-4o-mini", "gpt-5.4-nano",
        ])
        api_layout.addRow(UI["translate_model"] + ":", self._translate_model_combo)

        layout.addWidget(api_group)

        # OCR Endpoint (separate)
        ocr_group = QGroupBox("OCR 端點（選填，留空則使用上方 API）")
        ocr_layout = QFormLayout(ocr_group)
        ocr_layout.setSpacing(12)

        self._ocr_base_url_edit = QLineEdit()
        self._ocr_base_url_edit.setPlaceholderText("留空 = 使用上方 Base URL")
        self._ocr_base_url_edit.setToolTip(
            "如果 OCR 模型部署在不同的伺服器，請填寫\n"
            "例如：http://localhost:8000/v1（vLLM 本地部署）"
        )
        ocr_layout.addRow("OCR Base URL:", self._ocr_base_url_edit)

        self._ocr_api_key_edit = QLineEdit()
        self._ocr_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._ocr_api_key_edit.setPlaceholderText("留空 = 使用上方 API Key")
        ocr_layout.addRow("OCR API Key:", self._ocr_api_key_edit)

        self._structured_output_check = QCheckBox("使用 Structured Output（強制 JSON 格式）")
        self._structured_output_check.setToolTip(
            "啟用後 API 會以 JSON Schema 格式回傳結果\n"
            "PaddleOCR 模型會自動忽略此設定"
        )
        self._structured_output_check.setChecked(True)
        ocr_layout.addRow("", self._structured_output_check)

        layout.addWidget(ocr_group)

        # General
        general_group = QGroupBox(UI["settings_general"])
        general_layout = QFormLayout(general_group)
        general_layout.setSpacing(12)

        self._language_combo = QComboBox()
        self._language_combo.addItems(TARGET_LANGUAGES)
        general_layout.addRow(UI["default_language"] + ":", self._language_combo)

        self._render_scale_spin = QDoubleSpinBox()
        self._render_scale_spin.setRange(1.0, 4.0)
        self._render_scale_spin.setSingleStep(0.5)
        self._render_scale_spin.setDecimals(1)
        self._render_scale_spin.setToolTip(
            "OCR 時 PDF 渲染的解析度倍率\n"
            "越高越精準但越慢，建議 2.0"
        )
        general_layout.addRow(UI["pdf_scale"] + ":", self._render_scale_spin)

        layout.addWidget(general_group)

        # Capture
        capture_group = QGroupBox(UI["settings_capture"])
        capture_layout = QFormLayout(capture_group)
        capture_layout.setSpacing(12)

        self._hotkey_edit = QLineEdit()
        self._hotkey_edit.setPlaceholderText("Ctrl+Shift+O")
        self._hotkey_edit.setToolTip("隨時按下此快捷鍵即可截取螢幕區域進行 OCR")
        capture_layout.addRow(UI["hotkey"] + ":", self._hotkey_edit)

        self._auto_translate_check = QCheckBox(UI["auto_translate_capture"])
        capture_layout.addRow("", self._auto_translate_check)

        self._copy_clipboard_check = QCheckBox(UI["copy_to_clipboard"])
        capture_layout.addRow("", self._copy_clipboard_check)

        layout.addWidget(capture_group)

        # Startup
        startup_group = QGroupBox(UI["settings_startup"])
        startup_layout = QVBoxLayout(startup_group)

        self._start_minimized_check = QCheckBox(UI["start_minimized"])
        startup_layout.addWidget(self._start_minimized_check)

        self._start_with_windows_check = QCheckBox(UI["start_with_windows"])
        startup_layout.addWidget(self._start_with_windows_check)

        layout.addWidget(startup_group)

        # Save Button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton(UI["save"])
        save_btn.setFixedWidth(160)
        save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _load_settings(self):
        c = self._config
        self._api_key_edit.setText(c.get_api_key())
        self._base_url_edit.setText(c.get_base_url())
        self._ocr_model_combo.setCurrentText(str(c.get("openai/ocr_model", "gpt-4o")))
        self._translate_model_combo.setCurrentText(str(c.get("openai/translate_model", "gpt-4o")))
        self._language_combo.setCurrentText(str(c.get("general/target_language", "English")))
        self._render_scale_spin.setValue(float(c.get("general/pdf_render_scale", 2.0)))
        self._hotkey_edit.setText(c.get_hotkey())

        self._auto_translate_check.setChecked(
            c.get("capture/auto_translate") in (True, "true")
        )
        self._copy_clipboard_check.setChecked(
            c.get("capture/copy_to_clipboard", True) not in (False, "false")
        )
        self._start_minimized_check.setChecked(
            c.get("general/start_minimized") in (True, "true")
        )
        self._start_with_windows_check.setChecked(
            c.get("general/start_with_windows") in (True, "true")
        )

        # OCR endpoint
        self._ocr_base_url_edit.setText(str(c.get("ocr/base_url", "")))
        self._ocr_api_key_edit.setText(str(c.get("ocr/api_key", "")))
        self._structured_output_check.setChecked(
            c.get("ocr/structured_output", True) in (True, "true")
        )

    def _save_settings(self):
        c = self._config
        c.set("openai/api_key", self._api_key_edit.text().strip())
        c.set("openai/base_url", self._base_url_edit.text().strip() or "https://api.openai.com/v1")
        c.set("openai/ocr_model", self._ocr_model_combo.currentText())
        c.set("openai/translate_model", self._translate_model_combo.currentText())
        c.set("general/target_language", self._language_combo.currentText())
        c.set("general/pdf_render_scale", self._render_scale_spin.value())
        c.set("general/hotkey", self._hotkey_edit.text().strip())
        c.set("capture/auto_translate", self._auto_translate_check.isChecked())
        c.set("capture/copy_to_clipboard", self._copy_clipboard_check.isChecked())
        c.set("general/start_minimized", self._start_minimized_check.isChecked())
        c.set("general/start_with_windows", self._start_with_windows_check.isChecked())
        # OCR endpoint
        c.set("ocr/base_url", self._ocr_base_url_edit.text().strip())
        c.set("ocr/api_key", self._ocr_api_key_edit.text().strip())
        c.set("ocr/structured_output", self._structured_output_check.isChecked())
        self.settings_changed.emit()
        QMessageBox.information(self, UI["settings"], UI["settings_saved"])

    def _test_api_key(self):
        api_key = self._api_key_edit.text().strip()
        base_url = self._base_url_edit.text().strip() or "https://api.openai.com/v1"
        if not api_key:
            QMessageBox.warning(self, UI["test"], UI["no_api_key"])
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
            QMessageBox.information(self, UI["test"], UI["test_success"])
        except Exception as e:
            QMessageBox.critical(self, UI["test_fail"], str(e))
        finally:
            self._test_btn.setEnabled(True)
            self._test_btn.setText(UI["test"])
