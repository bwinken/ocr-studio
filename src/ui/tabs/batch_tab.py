"""Batch folder processing UI."""

from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.config import ConfigManager
from src.constants import TARGET_LANGUAGES, UI
from src.models import ExportSource, OverlayMode
from src.services.image_service import ImageService
from src.services.openai_service import OpenAIService
from src.services.pdf_service import PdfService
from src.workers.batch_worker import BatchWorker


class BatchTab(QWidget):
    def __init__(self, config: ConfigManager):
        super().__init__()
        self._config = config
        self._openai_service: OpenAIService | None = None
        self._pdf_service = PdfService(
            render_scale=float(config.get("general/pdf_render_scale", 2.0))
        )
        self._image_service = ImageService()
        self._worker: BatchWorker | None = None

        self._build_ui()

    def set_openai_service(self, service: OpenAIService):
        self._openai_service = service

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        # Settings group
        settings = QGroupBox(UI["settings"])
        form = QFormLayout(settings)
        form.setSpacing(12)

        # Input folder
        input_row = QHBoxLayout()
        self._input_edit = QLineEdit()
        self._input_edit.setPlaceholderText("選擇輸入資料夾...")
        self._input_edit.setReadOnly(True)
        input_row.addWidget(self._input_edit, 1)
        input_browse = QPushButton(UI["browse"])
        input_browse.setFixedWidth(80)
        input_browse.clicked.connect(self._browse_input)
        input_row.addWidget(input_browse)
        input_widget = QWidget()
        input_widget.setLayout(input_row)
        form.addRow(UI["input_folder"] + ":", input_widget)

        # Output folder
        output_row = QHBoxLayout()
        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("選擇輸出資料夾...")
        self._output_edit.setReadOnly(True)
        output_row.addWidget(self._output_edit, 1)
        output_browse = QPushButton(UI["browse"])
        output_browse.setFixedWidth(80)
        output_browse.clicked.connect(self._browse_output)
        output_row.addWidget(output_browse)
        output_widget = QWidget()
        output_widget.setLayout(output_row)
        form.addRow(UI["output_folder"] + ":", output_widget)

        # Target language
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(TARGET_LANGUAGES)
        default_lang = str(self._config.get("general/target_language", "English"))
        idx = self._lang_combo.findText(default_lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        form.addRow(UI["target_language"] + ":", self._lang_combo)

        # Overlay mode
        self._overlay_combo = QComboBox()
        self._overlay_combo.addItems([
            UI["overlay_visible"],
            UI["overlay_invisible"],
            UI["overlay_replace"],
        ])
        form.addRow(UI["overlay_mode"] + ":", self._overlay_combo)

        # Translate checkbox
        self._translate_check = QCheckBox(UI["do_translate"])
        self._translate_check.setChecked(True)
        form.addRow("", self._translate_check)

        layout.addWidget(settings)

        # Action buttons
        btn_row = QHBoxLayout()
        self._start_btn = QPushButton(UI["start"])
        self._start_btn.clicked.connect(self._start)
        btn_row.addWidget(self._start_btn)

        self._cancel_btn = QPushButton(UI["stop"])
        self._cancel_btn.setProperty("danger", True)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel)
        btn_row.addWidget(self._cancel_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Progress
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._detail_label = QLabel("")
        self._detail_label.setStyleSheet("color: #8181A5;")
        layout.addWidget(self._detail_label)

        # Log
        self._log = QListWidget()
        layout.addWidget(self._log, 1)

    def _browse_input(self):
        path = QFileDialog.getExistingDirectory(self, UI["input_folder"])
        if path:
            self._input_edit.setText(path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, UI["output_folder"])
        if path:
            self._output_edit.setText(path)

    def _start(self):
        input_path = self._input_edit.text().strip()
        output_path = self._output_edit.text().strip()

        if not input_path or not Path(input_path).is_dir():
            QMessageBox.warning(self, "錯誤", "請選擇有效的輸入資料夾")
            return
        if not output_path:
            QMessageBox.warning(self, "錯誤", "請選擇輸出資料夾")
            return
        if not self._openai_service or not self._openai_service.api_key:
            QMessageBox.warning(self, "錯誤", UI["no_api_key"])
            return

        overlay_map = {0: OverlayMode.VISIBLE, 1: OverlayMode.INVISIBLE, 2: OverlayMode.REPLACE}
        overlay_mode = overlay_map.get(self._overlay_combo.currentIndex(), OverlayMode.VISIBLE)

        export_source = ExportSource.TRANSLATED if self._translate_check.isChecked() else ExportSource.OCR

        self._log.clear()
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._start_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)

        self._worker = BatchWorker(
            openai_service=self._openai_service,
            pdf_service=self._pdf_service,
            image_service=self._image_service,
            input_folder=Path(input_path),
            output_folder=Path(output_path),
            target_lang=self._lang_combo.currentText(),
            overlay_mode=overlay_mode,
            export_source=export_source,
            do_translate=self._translate_check.isChecked(),
        )
        self._worker.file_started.connect(self._on_file_started)
        self._worker.file_completed.connect(self._on_file_completed)
        self._worker.file_failed.connect(self._on_file_failed)
        self._worker.all_completed.connect(self._on_all_completed)
        self._worker.progress_detail.connect(self._on_detail)
        self._worker.start()

    def _cancel(self):
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._detail_label.setText("正在取消...")

    @Slot(str, int, int)
    def _on_file_started(self, filename: str, current: int, total: int):
        self._progress.setMaximum(total)
        self._progress.setValue(current - 1)
        self._detail_label.setText(f"處理中 {filename} ({current}/{total})")

    @Slot(str)
    def _on_file_completed(self, filename: str):
        item = QListWidgetItem(f"[OK] {filename}")
        item.setForeground(Qt.GlobalColor.green)
        self._log.addItem(item)
        self._log.scrollToBottom()

    @Slot(str, str)
    def _on_file_failed(self, filename: str, error: str):
        item = QListWidgetItem(f"[FAIL] {filename} - {error}")
        item.setForeground(Qt.GlobalColor.red)
        self._log.addItem(item)
        self._log.scrollToBottom()

    @Slot(int, int)
    def _on_all_completed(self, success: int, failed: int):
        self._progress.setValue(self._progress.maximum())
        self._start_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._detail_label.setText(
            UI["batch_complete"].format(success=success, failed=failed)
        )
        self._worker = None

    @Slot(str)
    def _on_detail(self, text: str):
        self._detail_label.setText(text)
