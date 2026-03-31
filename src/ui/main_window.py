"""Main window: home page always visible, features open as separate windows."""

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

_TITLE_BAR_H = 38
_RESIZE_MARGIN = 6


class FeatureWindow(QWidget):
    """Reusable window with custom title bar matching main window."""

    def __init__(self, title: str, widget: QWidget, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setWindowTitle(f"{APP_NAME} — {title}")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)
        self._drag_pos = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Custom title bar
        header = QWidget()
        header.setObjectName("titleBar")
        header.setFixedHeight(38)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 0, 0, 0)
        hl.setSpacing(0)

        title_label = QLabel(f"{APP_NAME} — {title}")
        title_label.setObjectName("appName")
        hl.addWidget(title_label)
        hl.addStretch()

        for text, slot, name in [
            ("\u2013", self.showMinimized, "winMin"),
            ("\u25A1", self._toggle_max, "winMax"),
            ("\u2715", self.close, "winClose"),
        ]:
            btn = QPushButton(text)
            btn.setObjectName(name)
            btn.setFixedSize(46, 38)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            hl.addWidget(btn)

        layout.addWidget(header)
        layout.addWidget(widget, 1)
        self._header = header

    def _toggle_max(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def mousePressEvent(self, event):
        if event.position().y() < 38:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class MainWindow(QWidget):
    def __init__(self, config: ConfigManager):
        super().__init__()
        self._config = config
        self._active_workers = []

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowMinimizeButtonHint)
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(60, 300)
        self.resize(760, 600)
        self._compact = False

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

        self._title_bar_widget = self._build_title_bar()
        root.addWidget(self._title_bar_widget)

        # Stack: setup / home / compact sidebar
        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        self._setup_page = SetupPage(config)
        self._setup_page.setup_complete.connect(self._on_setup_complete)
        self._stack.addWidget(self._setup_page)  # index 0

        self._home_page = HomePage(config)
        self._home_page.capture_requested.connect(self._start_capture_with_mode)
        self._home_page.document_clicked.connect(self._open_documents)
        self._home_page.batch_clicked.connect(self._open_batch)
        self._home_page.settings_clicked.connect(self._open_settings)
        self._stack.addWidget(self._home_page)  # index 1

        self._sidebar = self._build_compact_sidebar()
        self._stack.addWidget(self._sidebar)  # index 2

        self._status_bar_widget = self._build_status_bar()
        root.addWidget(self._status_bar_widget)

        # ── Feature windows (lazy-created) ──
        self._doc_window: FeatureWindow | None = None
        self._batch_window: FeatureWindow | None = None
        self._settings_window: FeatureWindow | None = None

        # Initial
        self._stack.setCurrentIndex(1 if config.get_api_key() else 0)
        self._update_connection_indicator()
        self._apply_theme(str(config.get("general/theme", "light")))
        self._set_status(UI["ready"])

    # ── Frameless resize ──

    def nativeEvent(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == 0x0084:
                result = self._hit_test(self.mapFromGlobal(QCursor.pos()))
                if result:
                    return True, result
        return super().nativeEvent(eventType, message)

    def _hit_test(self, pos):
        M = _RESIZE_MARGIN
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        l, r, t, b = x < M, x > w - M, y < M, y > h - M
        if t and l: return 13
        if t and r: return 14
        if b and l: return 16
        if b and r: return 17
        if l: return 10
        if r: return 11
        if t: return 12
        if b: return 15
        if self._compact:
            # In compact mode: grip area (top 36px) is draggable
            if y < 36:
                return 2  # HTCAPTION
        elif y < _TITLE_BAR_H:
            child = self._title_bar.childAt(self._title_bar.mapFromParent(pos))
            if not child or not isinstance(child, QPushButton):
                return 2
        return 0

    # ── Title Bar ──

    def _build_title_bar(self) -> QWidget:
        self._title_bar = QWidget()
        self._title_bar.setObjectName("titleBar")
        self._title_bar.setFixedHeight(_TITLE_BAR_H)
        h = QHBoxLayout(self._title_bar)
        h.setContentsMargins(14, 0, 0, 0)
        h.setSpacing(0)

        self._header_title = QLabel(APP_NAME)
        self._header_title.setObjectName("appName")
        h.addWidget(self._header_title)

        h.addStretch()

        # Connection status
        self._conn_dot = QLabel("\u25CF")
        self._conn_dot.setObjectName("connDot")
        h.addWidget(self._conn_dot)
        self._conn_label = QLabel("")
        self._conn_label.setObjectName("connModel")
        h.addWidget(self._conn_label)

        # Theme toggle
        self._theme_btn = QPushButton("\u263E")
        self._theme_btn.setObjectName("winMin")
        self._theme_btn.setFixedSize(36, _TITLE_BAR_H)
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_btn.setToolTip("切換深色 / 淺色模式")
        self._theme_btn.clicked.connect(self._toggle_theme)
        h.addWidget(self._theme_btn)

        # Compact mode button
        compact_btn = QPushButton("\u00AB")  # « collapse
        compact_btn.setObjectName("winMin")
        compact_btn.setFixedSize(36, _TITLE_BAR_H)
        compact_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        compact_btn.setToolTip("收起為迷你工具列")
        compact_btn.clicked.connect(self.toggle_compact)
        h.addWidget(compact_btn)

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
        self.showNormal() if self.isMaximized() else self.showMaximized()

    # ── Compact sidebar ──

    _COMPACT_THRESHOLD = 200  # width below this → compact mode

    def _build_compact_sidebar(self) -> QWidget:
        """Vertical icon strip — compact mode."""
        sidebar = QWidget()
        sidebar.setObjectName("titleBar")  # reuse title bar bg for theme-aware color
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(6, 6, 6, 10)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        # Drag handle — hold here to move window
        grip = QLabel("\u2630")  # ☰ hamburger
        grip.setObjectName("sidebarGrip")
        grip.setFixedSize(48, 30)
        grip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grip.setCursor(Qt.CursorShape.OpenHandCursor)
        lay.addWidget(grip)

        # Expand button
        expand_btn = self._make_sidebar_btn("\u00BB", "展開視窗")  # »
        expand_btn.clicked.connect(self.toggle_compact)
        lay.addWidget(expand_btn)

        lay.addSpacing(6)

        icons = [
            ("\u2702", "截圖", self._sidebar_capture),         # ✂
            ("\U0001F4C4", "文件處理", self._open_documents),   # 📄
            ("\U0001F4C2", "批次處理", self._open_batch),       # 📂
            ("\u2699", "設定", self._open_settings),             # ⚙
        ]
        for icon, tip, slot in icons:
            btn = self._make_sidebar_btn(icon, tip)
            btn.clicked.connect(slot)
            lay.addWidget(btn)

        lay.addStretch()

        self._sidebar_theme_btn = self._make_sidebar_btn("\u263E", "切換主題")
        self._sidebar_theme_btn.clicked.connect(self._toggle_theme)
        lay.addWidget(self._sidebar_theme_btn)

        # Close
        close_btn = self._make_sidebar_btn("\u2715", "關閉")
        close_btn.clicked.connect(self.close)
        lay.addWidget(close_btn)

        return sidebar

    @staticmethod
    def _make_sidebar_btn(icon: str, tooltip: str) -> QPushButton:
        btn = QPushButton(icon)
        btn.setObjectName("sidebarBtn")
        btn.setFixedSize(48, 44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        return btn

    def _sidebar_capture(self):
        """Capture using home page toggle state."""
        self.start_screen_capture()

    def toggle_compact(self):
        """Switch between full home page and compact icon strip."""
        if self._compact:
            # Expand
            self._compact = False
            self._title_bar_widget.show()
            self._status_bar_widget.show()
            if self._config.get_api_key():
                self._stack.setCurrentIndex(1)
            else:
                self._stack.setCurrentIndex(0)
            self.resize(760, 600)
        else:
            # Compact
            self._compact = True
            self._title_bar_widget.hide()
            self._status_bar_widget.hide()
            self._stack.setCurrentIndex(2)
            self.resize(68, 320)

    def _toggle_theme(self):
        current = str(self._config.get("general/theme", "light"))
        new_theme = "dark" if current == "light" else "light"
        self._config.set("general/theme", new_theme)
        self._apply_theme(new_theme)

    def _apply_theme(self, theme: str):
        from src.ui.styles import LIGHT_THEME, DARK_THEME
        QApplication.instance().setStyleSheet(DARK_THEME if theme == "dark" else LIGHT_THEME)
        icon = "\u2600" if theme == "dark" else "\u263E"
        tip = "切換至淺色模式" if theme == "dark" else "切換至深色模式"
        self._theme_btn.setText(icon)
        self._theme_btn.setToolTip(tip)
        self._sidebar_theme_btn.setText(icon)
        self._sidebar_theme_btn.setToolTip(tip)

    # ── Status Bar ──

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("statusBar")
        bar.setFixedHeight(24)
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(8)

        self._status_msg = QLabel(UI["ready"])
        self._status_msg.setObjectName("textSecondary")
        self._status_msg.setStyleSheet("font-size: 11px;")
        h.addWidget(self._status_msg)

        h.addStretch()

        hotkey = str(self._config.get_hotkey())
        hint = QLabel(f"{hotkey}")
        hint.setObjectName("textDimmed")
        hint.setStyleSheet("font-size: 11px;")
        h.addWidget(hint)

        sep = QLabel("\u00B7")
        sep.setObjectName("textDimmed")
        sep.setStyleSheet("font-size: 11px;")
        h.addWidget(sep)

        ver = QLabel(f"v{APP_VERSION}")
        ver.setObjectName("textDimmed")
        ver.setStyleSheet("font-size: 11px;")
        h.addWidget(ver)

        return bar

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

    # ── Open feature windows ──

    def _open_documents(self):
        if not self._doc_window:
            from src.ui.tabs.documents_tab import DocumentsTab
            self.documents_tab = DocumentsTab(self._config)
            self.documents_tab.set_openai_service(self._openai_service)
            self._doc_window = FeatureWindow(UI["documents_title"], self.documents_tab)
        self._doc_window.show()
        self._doc_window.raise_()
        self._doc_window.activateWindow()

    def _open_batch(self):
        if not self._batch_window:
            from src.ui.tabs.batch_tab import BatchTab
            self.batch_tab = BatchTab(self._config)
            self.batch_tab.set_openai_service(self._openai_service)
            self._batch_window = FeatureWindow(UI["batch_title"], self.batch_tab)
        self._batch_window.show()
        self._batch_window.raise_()
        self._batch_window.activateWindow()

    def _open_settings(self):
        if not self._settings_window:
            from src.ui.tabs.settings_tab import SettingsTab
            self.settings_tab = SettingsTab(self._config)
            self.settings_tab.settings_changed.connect(self._on_settings_changed)
            self._settings_window = FeatureWindow(UI["settings_title"], self.settings_tab)
        self._settings_window.show()
        self._settings_window.raise_()
        self._settings_window.activateWindow()

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
        self._update_connection_indicator()
        self._stack.setCurrentIndex(1)
        self._set_status(UI["settings_saved"])

    # ── Capture flow ──
    # _capture_mode: "screenshot" | "ocr" | "ocr+translate"
    # _capture_lang: target language for translate mode

    @Slot()
    def start_screen_capture(self):
        """Triggered by global hotkey — uses home page toggle state."""
        home = self._home_page
        ocr = home._ocr_toggle.isChecked()
        translate = home._translate_toggle.isChecked()
        lang = home._lang_combo.currentText()
        if translate and ocr:
            mode = "ocr+translate"
        elif ocr:
            mode = "ocr"
        else:
            mode = "screenshot"
        self._start_capture_with_mode(mode, lang)

    @Slot(str, str)
    def _start_capture_with_mode(self, mode: str, lang: str):
        self._capture_mode = mode
        self._capture_lang = lang
        if mode != "screenshot" and not self._config.get_api_key():
            self._set_status(UI["no_api_key"])
            self._stack.setCurrentIndex(0)
            return
        self._set_status("截圖中...")
        self._capture_overlay.start_capture()

    @Slot(QRect)
    def _on_region_captured(self, rect: QRect):
        image_bytes = self._screen_svc.capture_region(
            rect.x(), rect.y(), rect.width(), rect.height()
        )
        self._last_capture_bytes = image_bytes
        mode = getattr(self, "_capture_mode", "ocr")

        if mode == "screenshot":
            # Just copy image to clipboard, no popup
            from PySide6.QtGui import QImage
            img = QImage.fromData(image_bytes)
            QApplication.clipboard().setImage(img)
            self._set_status("截圖已複製到剪貼簿")
            return

        # OCR or OCR+translate → show spinner popup, start OCR
        self._set_status("OCR 辨識中...")
        show_translate = (mode == "ocr+translate")
        self._capture_result.show_processing(image_bytes, show_translate)

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
        mode = getattr(self, "_capture_mode", "ocr")

        if self._last_capture_bytes:
            self._capture_result.set_capture(self._last_capture_bytes, text)

        if mode == "ocr+translate" and text:
            # Auto-translate, then copy translated text
            self._set_status("自動翻譯中...")
            self._capture_result._processing_row.show()
            self._capture_result._spinner.start()
            self._capture_result._processing_label.setText("翻譯中...")
            lang = getattr(self, "_capture_lang", "English")
            worker = TranslateWorker(self._openai_service, text, lang)
            worker.finished.connect(self._on_capture_translate_done)
            worker.error.connect(self._on_capture_translate_error)
            self._active_workers.append(worker)
            worker.start()
        else:
            # OCR only → copy OCR text
            if text:
                QApplication.clipboard().setText(text)
                self._set_status("OCR 完成，已複製到剪貼簿")

        self._cleanup_worker(self.sender())

    @Slot(int, str)
    def _on_capture_ocr_error(self, page_index, error_msg):
        self._set_status(f"OCR 錯誤：{error_msg}")
        self._capture_result.set_capture(self._last_capture_bytes or b"", f"OCR 錯誤：{error_msg}")
        self._cleanup_worker(self.sender())

    @Slot(str, str)
    def _on_capture_translate(self, text: str, target_lang: str):
        """Manual translate from popup button."""
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
        self._capture_result.set_translation(translated_text)
        # Auto-copy translated text to clipboard
        QApplication.clipboard().setText(translated_text)
        self._set_status("翻譯完成，已複製到剪貼簿")
        self._cleanup_worker(self.sender())

    @Slot(int, str)
    def _on_capture_translate_error(self, page_index, error_msg):
        self._set_status(f"翻譯錯誤：{error_msg}")
        self._capture_result.set_translation_error(error_msg)
        self._cleanup_worker(self.sender())

    @Slot()
    def _on_settings_changed(self):
        self._openai_service = self._build_openai_service()
        if self._doc_window:
            self.documents_tab.set_openai_service(self._openai_service)
        if self._batch_window:
            self.batch_tab.set_openai_service(self._openai_service)
        self._update_connection_indicator()
        self._set_status(UI["settings_saved"])
        # Notify hotkey updater
        if hasattr(self, "_hotkey_settings_callback"):
            self._hotkey_settings_callback()

    def _cleanup_worker(self, worker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
