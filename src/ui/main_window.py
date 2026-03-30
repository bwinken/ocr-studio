"""Main window: frameless, custom title bar, Google-style layout."""

import ctypes
import ctypes.wintypes

from PySide6.QtCore import QRect, Qt, Slot
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.config import ConfigManager
from src.constants import APP_NAME, APP_VERSION, UI
from src.services.openai_service import OpenAIService
from src.services.screen_capture import ScreenCaptureService
from src.ui.capture_overlay import CaptureOverlay
from src.ui.capture_result_widget import CaptureResultWidget
from src.ui.home_page import HomePage
from src.ui.setup_page import SetupPage
from src.workers.ocr_worker import OcrWorker
from src.workers.translate_worker import TranslateWorker

PAGE_SETUP = 0
PAGE_HOME = 1
PAGE_CAPTURE = 2
PAGE_DOCUMENTS = 3
PAGE_BATCH = 4
PAGE_SETTINGS = 5

_PAGE_TITLES = {
    PAGE_CAPTURE: UI["capture_title"],
    PAGE_DOCUMENTS: UI["documents_title"],
    PAGE_BATCH: UI["batch_title"],
    PAGE_SETTINGS: UI["settings_title"],
}

_TITLE_BAR_H = 38
_RESIZE_MARGIN = 6


class MainWindow(QWidget):
    def __init__(self, config: ConfigManager):
        super().__init__()
        self._config = config
        self._active_workers = []

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowMinimizeButtonHint)
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)

        # Services
        self._openai_service = self._build_openai_service()
        self._screen_svc = ScreenCaptureService()

        # Capture overlay + result popup
        self._capture_overlay = CaptureOverlay()
        self._capture_overlay.region_selected.connect(self._on_region_captured)
        self._capture_overlay.cancelled.connect(self._on_capture_cancelled)
        self._capture_result = CaptureResultWidget(config)
        self._capture_result.translate_requested.connect(self._on_capture_translate)
        self._last_capture_bytes: bytes | None = None

        # ── Layout ──
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_title_bar())

        self._stack = QStackedWidget()
        self._stack.currentChanged.connect(self._on_page_changed)
        root.addWidget(self._stack, 1)

        root.addWidget(self._build_status_bar())

        # ── Pages ──
        self._setup_page = SetupPage(config)
        self._setup_page.setup_complete.connect(self._on_setup_complete)
        self._stack.addWidget(self._setup_page)

        self._home_page = HomePage(config)
        self._home_page.capture_clicked.connect(self.start_screen_capture)
        self._home_page.document_clicked.connect(lambda: self._stack.setCurrentIndex(PAGE_DOCUMENTS))
        self._home_page.batch_clicked.connect(lambda: self._stack.setCurrentIndex(PAGE_BATCH))
        self._home_page.settings_clicked.connect(lambda: self._stack.setCurrentIndex(PAGE_SETTINGS))
        self._stack.addWidget(self._home_page)

        from src.ui.tabs.capture_tab import CaptureTab
        self.capture_tab = CaptureTab(config)
        self._stack.addWidget(self.capture_tab)

        from src.ui.tabs.documents_tab import DocumentsTab
        self.documents_tab = DocumentsTab(config)
        self.documents_tab.set_openai_service(self._openai_service)
        self._stack.addWidget(self.documents_tab)

        from src.ui.tabs.batch_tab import BatchTab
        self.batch_tab = BatchTab(config)
        self.batch_tab.set_openai_service(self._openai_service)
        self._stack.addWidget(self.batch_tab)

        from src.ui.tabs.settings_tab import SettingsTab
        self.settings_tab = SettingsTab(config)
        self.settings_tab.settings_changed.connect(self._on_settings_changed)
        self._stack.addWidget(self.settings_tab)

        # Initial
        self._stack.setCurrentIndex(PAGE_HOME if config.get_api_key() else PAGE_SETUP)
        self._update_connection_indicator()
        self._set_status(UI["ready"])

    # ── Frameless resize via Windows native events ──

    def nativeEvent(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == 0x0084:  # WM_NCHITTEST
                result = self._hit_test(self.mapFromGlobal(QCursor.pos()))
                if result:
                    return True, result
        return super().nativeEvent(eventType, message)

    def _hit_test(self, pos):
        M = _RESIZE_MARGIN
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()

        l, r, t, b = x < M, x > w - M, y < M, y > h - M
        if t and l: return 13  # TOPLEFT
        if t and r: return 14  # TOPRIGHT
        if b and l: return 16  # BOTTOMLEFT
        if b and r: return 17  # BOTTOMRIGHT
        if l: return 10
        if r: return 11
        if t: return 12
        if b: return 15

        # Title bar drag (except over buttons)
        if y < _TITLE_BAR_H:
            child = self._title_bar.childAt(self._title_bar.mapFromParent(pos))
            if not child or not isinstance(child, QPushButton):
                return 2  # HTCAPTION
        return 0

    # ── Title Bar ──

    def _build_title_bar(self) -> QWidget:
        self._title_bar = QWidget()
        self._title_bar.setObjectName("titleBar")
        self._title_bar.setFixedHeight(_TITLE_BAR_H)
        h = QHBoxLayout(self._title_bar)
        h.setContentsMargins(14, 0, 0, 0)
        h.setSpacing(0)

        # Back button
        self._back_btn = QPushButton("\u2190")
        self._back_btn.setObjectName("winMin")  # reuse transparent style
        self._back_btn.setFixedSize(32, 28)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(PAGE_HOME))
        self._back_btn.hide()
        h.addWidget(self._back_btn)

        self._header_title = QLabel(APP_NAME)
        self._header_title.setObjectName("appName")
        h.addWidget(self._header_title)

        self._nav_sep = QLabel("/")
        self._nav_sep.setObjectName("navSep")
        self._nav_sep.hide()
        h.addWidget(self._nav_sep)

        self._nav_page = QLabel("")
        self._nav_page.setObjectName("navPage")
        self._nav_page.hide()
        h.addWidget(self._nav_page)

        h.addStretch()

        # Connection status
        self._conn_dot = QLabel("\u25CF")
        self._conn_dot.setObjectName("connDot")
        h.addWidget(self._conn_dot)

        self._conn_label = QLabel("")
        self._conn_label.setObjectName("connModel")
        h.addWidget(self._conn_label)

        # Window controls
        for text, slot, name in [
            ("\u2013", self.showMinimized, "winMin"),
            ("\u25A1", self._toggle_max, "winMax"),
            ("\u2715", self.close, "winClose"),
        ]:
            btn = QPushButton(text)
            btn.setObjectName(name)
            btn.setFixedSize(46, _TITLE_BAR_H)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        return self._title_bar

    def _toggle_max(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ── Status Bar ──

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("statusBar")
        bar.setFixedHeight(24)
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(8)

        self._status_msg = QLabel(UI["ready"])
        self._status_msg.setStyleSheet("color: #8181A5; font-size: 11px;")
        h.addWidget(self._status_msg)

        h.addStretch()

        hotkey = str(self._config.get_hotkey())
        hint = QLabel(f"{hotkey}")
        hint.setStyleSheet("color: #ADADC0; font-size: 11px;")
        h.addWidget(hint)

        sep = QLabel("\u00B7")
        sep.setStyleSheet("color: #DDDDE5; font-size: 11px;")
        h.addWidget(sep)

        ver = QLabel(f"v{APP_VERSION}")
        ver.setStyleSheet("color: #ADADC0; font-size: 11px;")
        h.addWidget(ver)

        return bar

    # ── Navigation ──

    def _on_page_changed(self, index: int):
        is_sub = index not in (PAGE_SETUP, PAGE_HOME)
        self._back_btn.setVisible(is_sub)
        self._nav_sep.setVisible(is_sub)
        self._nav_page.setVisible(is_sub)
        if is_sub:
            self._nav_page.setText(_PAGE_TITLES.get(index, ""))

    # ── Status helpers ──

    def _set_status(self, msg: str):
        self._status_msg.setText(msg)

    def _update_connection_indicator(self):
        has_key = bool(self._config.get_api_key())
        model = str(self._config.get("openai/ocr_model", "gpt-4o"))
        if has_key:
            self._conn_dot.setStyleSheet("color: #006F0C; font-size: 8px;")
            self._conn_label.setText(model)
        else:
            self._conn_dot.setStyleSheet("color: #D93025; font-size: 8px;")
            self._conn_label.setText("API 未設定")

    # ── Service ──

    def _build_openai_service(self) -> OpenAIService:
        c = self._config
        return OpenAIService(
            api_key=c.get_api_key(),
            base_url=c.get_base_url(),
            ocr_model=str(c.get("openai/ocr_model", "gpt-4o")),
            translate_model=str(c.get("openai/translate_model", "gpt-4o")),
            max_tokens=int(c.get("openai/max_tokens", 4096)),
            temperature_ocr=float(c.get("openai/temperature_ocr", 0.1)),
            temperature_translate=float(c.get("openai/temperature_translate", 0.3)),
            ocr_base_url=str(c.get("ocr/base_url", "")),
            ocr_api_key=str(c.get("ocr/api_key", "")),
            use_structured_output=c.get("ocr/structured_output", True) in (True, "true"),
        )

    # ── Slots ──

    @Slot()
    def _on_setup_complete(self):
        self._openai_service = self._build_openai_service()
        self.documents_tab.set_openai_service(self._openai_service)
        self.batch_tab.set_openai_service(self._openai_service)
        self._update_connection_indicator()
        self._stack.setCurrentIndex(PAGE_HOME)
        self._set_status(UI["settings_saved"])

    @Slot()
    def start_screen_capture(self):
        if not self._config.get_api_key():
            self._set_status(UI["no_api_key"])
            self._stack.setCurrentIndex(PAGE_SETUP)
            return
        self._set_status("截圖中...")
        self._capture_overlay.start_capture()

    @Slot(QRect)
    def _on_region_captured(self, rect: QRect):
        self._set_status("OCR 辨識中...")
        image_bytes = self._screen_svc.capture_region(
            rect.x(), rect.y(), rect.width(), rect.height()
        )
        self._last_capture_bytes = image_bytes
        if not self._openai_service.api_key:
            self._set_status(UI["no_api_key"])
            return
        worker = OcrWorker(self._openai_service, image_bytes)
        worker.finished.connect(self._on_capture_ocr_done)
        worker.error.connect(self._on_capture_ocr_error)
        worker.progress.connect(self._set_status)
        self._active_workers.append(worker)
        worker.start()

    @Slot()
    def _on_capture_cancelled(self):
        self._set_status("已取消截圖")

    @Slot(int, list, str)
    def _on_capture_ocr_done(self, page_index, blocks, text):
        self._set_status(f"OCR 完成 — {len(blocks)} 個文字區塊")
        if self._last_capture_bytes:
            self._capture_result.set_capture(self._last_capture_bytes, text)
            self.capture_tab.add_capture_result(self._last_capture_bytes, text, blocks)
            copy_enabled = self._config.get("capture/copy_to_clipboard")
            if (copy_enabled is True or copy_enabled == "true") and text:
                QApplication.clipboard().setText(text)
            self._stack.setCurrentIndex(PAGE_CAPTURE)
        self._cleanup_worker(self.sender())

    @Slot(int, str)
    def _on_capture_ocr_error(self, page_index, error_msg):
        self._set_status(f"OCR 錯誤：{error_msg}")
        self._cleanup_worker(self.sender())

    @Slot(str, str)
    def _on_capture_translate(self, text: str, target_lang: str):
        if not self._openai_service.api_key:
            self._capture_result.set_translation_error(UI["no_api_key"])
            return
        worker = TranslateWorker(self._openai_service, text, target_lang)
        worker.finished.connect(self._on_capture_translate_done)
        worker.error.connect(self._on_capture_translate_error)
        worker.progress.connect(self._set_status)
        self._active_workers.append(worker)
        worker.start()

    @Slot(int, str)
    def _on_capture_translate_done(self, page_index, translated_text):
        self._set_status("翻譯完成")
        self._capture_result.set_translation(translated_text)
        self._cleanup_worker(self.sender())

    @Slot(int, str)
    def _on_capture_translate_error(self, page_index, error_msg):
        self._set_status(f"翻譯錯誤：{error_msg}")
        self._capture_result.set_translation_error(error_msg)
        self._cleanup_worker(self.sender())

    @Slot()
    def _on_settings_changed(self):
        self._openai_service = self._build_openai_service()
        self.documents_tab.set_openai_service(self._openai_service)
        self.batch_tab.set_openai_service(self._openai_service)
        self._update_connection_indicator()
        self._set_status(UI["settings_saved"])

    def _cleanup_worker(self, worker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
