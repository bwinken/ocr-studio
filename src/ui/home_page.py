"""Home page — intro banner + action cards. Capture card has inline toggles."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.constants import TARGET_LANGUAGES, UI

_ACCENTS = {
    "indigo": "#0B28D3",
    "violet": "#7B1FA2",
    "amber": "#E8710A",
    "teal": "#00897B",
}


class ToggleChip(QPushButton):
    """Small pill toggle chip — uses objectName for theme-aware on/off."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(26)
        self._refresh()
        self.toggled.connect(lambda _: self._refresh())

    def _refresh(self):
        # on = primary fill, off = secondary outline (both theme-aware via QSS)
        if self.isChecked():
            self.setProperty("secondary", False)
            self.setStyleSheet(
                "QPushButton { border-radius: 13px; padding: 2px 14px; "
                "font-size: 11px; font-weight: 600; }"
            )
        else:
            self.setProperty("secondary", True)
            self.setStyleSheet(
                "QPushButton { border-radius: 13px; padding: 2px 14px; "
                "font-size: 11px; font-weight: 500; }"
            )


class ActionCard(QPushButton):
    """Standard card for non-capture features."""

    def __init__(self, icon: str, title: str, desc: str,
                 accent: str, badge: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("actionCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(76)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 14, 16, 14)
        row.setSpacing(14)

        ic = QLabel(icon)
        ic.setFixedSize(44, 44)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet(
            f"font-size: 22px; background-color: {accent}14; "
            f"border-radius: 12px; border: none; color: {accent};"
        )
        ic.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(ic)

        col = QVBoxLayout()
        col.setSpacing(2)
        col.setContentsMargins(0, 0, 0, 0)

        t = QLabel(title)
        t.setObjectName("textPrimary")
        t.setStyleSheet("font-size: 17px; font-weight: 700; background: transparent; border: none;")
        t.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        col.addWidget(t)

        d = QLabel(desc)
        d.setObjectName("textSecondary")
        d.setWordWrap(True)
        d.setStyleSheet("font-size: 13px; background: transparent; border: none;")
        d.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        col.addWidget(d)

        row.addLayout(col, 1)

        if badge:
            b = QLabel(badge)
            b.setObjectName("textDimmed")
            b.setStyleSheet(
                "font-size: 10px; background: transparent; border: none;"
            )
            b.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            row.addWidget(b, 0, Qt.AlignmentFlag.AlignVCenter)

        arrow = QLabel("\u203A")
        arrow.setObjectName("textDimmed")
        arrow.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(arrow, 0, Qt.AlignmentFlag.AlignVCenter)


class HomePage(QWidget):
    capture_requested = Signal(str, str)  # (mode, lang)
    document_clicked = Signal()
    batch_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 28, 40, 28)
        layout.setSpacing(0)

        # ── Banner ──
        banner = QWidget()
        banner.setObjectName("bannerBg")
        banner.setMinimumHeight(90)
        bl = QVBoxLayout(banner)
        bl.setContentsMargins(28, 20, 28, 20)
        bl.setSpacing(8)

        title = QLabel("OCR Studio")
        title.setObjectName("textAccent")
        title.setStyleSheet("font-size: 24px; font-weight: 700; background: transparent;")
        title.setMinimumHeight(32)
        bl.addWidget(title)

        intro = QLabel(
            "智能文件辨識與翻譯工具 — 截圖 OCR、PDF / 圖片辨識、批次處理與多語言翻譯"
        )
        intro.setObjectName("textSecondary")
        intro.setWordWrap(True)
        intro.setStyleSheet("font-size: 14px; background: transparent;")
        bl.addWidget(intro)

        layout.addWidget(banner)
        layout.addSpacing(16)

        section = QLabel("選擇功能")
        section.setObjectName("textSecondary")
        section.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(section)
        layout.addSpacing(8)

        # ── Capture card (custom — has toggles inside) ──
        self._capture_card = QPushButton()
        self._capture_card.setObjectName("actionCard")
        self._capture_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._capture_card.setFixedHeight(80)
        self._capture_card.setCursor(Qt.CursorShape.PointingHandCursor)
        self._capture_card.clicked.connect(self._do_capture)

        card_layout = QHBoxLayout(self._capture_card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(14)

        ic = QLabel("\U0001F5BC")
        ic.setFixedSize(44, 44)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet(
            f"font-size: 22px; background-color: {_ACCENTS['indigo']}14; "
            f"border-radius: 12px; border: none; color: {_ACCENTS['indigo']};"
        )
        ic.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        card_layout.addWidget(ic)

        col = QVBoxLayout()
        col.setSpacing(4)
        col.setContentsMargins(0, 0, 0, 0)

        # Title + description
        t = QLabel("截圖")
        t.setObjectName("textPrimary")
        t.setStyleSheet("font-size: 17px; font-weight: 700; background: transparent; border: none;")
        t.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        col.addWidget(t)

        hotkey = str(self._config.get_hotkey())
        d = QLabel(f"框選螢幕區域，即時辨識文字並翻譯  {hotkey}")
        d.setObjectName("textSecondary")
        d.setStyleSheet("font-size: 13px; background: transparent; border: none;")
        d.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        col.addWidget(d)

        card_layout.addLayout(col, 1)

        # Right side: toggle chips + lang combo
        self._ocr_toggle = ToggleChip("OCR")
        self._ocr_toggle.setToolTip("啟用：截圖後自動 OCR，文字複製到剪貼簿")
        self._ocr_toggle.setChecked(True)
        card_layout.addWidget(self._ocr_toggle, 0, Qt.AlignmentFlag.AlignVCenter)

        self._translate_toggle = ToggleChip("翻譯")
        self._translate_toggle.setToolTip("啟用：OCR 後自動翻譯，翻譯結果複製到剪貼簿")
        self._translate_toggle.toggled.connect(self._on_translate_toggled)
        card_layout.addWidget(self._translate_toggle, 0, Qt.AlignmentFlag.AlignVCenter)

        self._lang_combo = QComboBox()
        self._lang_combo.setToolTip("翻譯目標語言")
        self._lang_combo.addItems(TARGET_LANGUAGES)
        default_lang = str(self._config.get("general/target_language", "English"))
        idx = self._lang_combo.findText(default_lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.setFixedHeight(26)
        self._lang_combo.setStyleSheet(
            "QComboBox { border-radius: 13px; padding: 2px 10px; "
            "font-size: 11px; min-width: 60px; }"
        )
        self._lang_combo.setVisible(False)
        card_layout.addWidget(self._lang_combo, 0, Qt.AlignmentFlag.AlignVCenter)

        arrow = QLabel("\u203A")
        arrow.setObjectName("textDimmed")
        arrow.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        card_layout.addWidget(arrow, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self._capture_card)
        layout.addSpacing(10)

        # ── Other feature cards ──
        cards_data = [
            ("\U0001F4C4", UI["document_title"],
             "拖放 PDF 或圖片，OCR 辨識後翻譯並匯出",
             _ACCENTS["violet"], "PDF・PNG・JPG", self.document_clicked),
            ("\U0001F4C2", UI["batch_title"],
             "選擇資料夾，一次處理所有文件",
             _ACCENTS["amber"], "", self.batch_clicked),
            ("\u2699", UI["settings_title"],
             "API 連線、模型、語言與快捷鍵",
             _ACCENTS["teal"], "", self.settings_clicked),
        ]

        for icon, title, desc, accent, badge, sig in cards_data:
            card = ActionCard(icon, title, desc, accent, badge)
            card.clicked.connect(sig.emit)
            layout.addWidget(card)
            layout.addSpacing(10)

        layout.addStretch()

        tip = QLabel("首次使用？請先到「設定」設定 API 連線")
        tip.setObjectName("textDimmed")
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip.setStyleSheet("font-size: 11px;")
        layout.addWidget(tip)

    # ── Slots ──

    def _on_translate_toggled(self, checked: bool):
        self._lang_combo.setVisible(checked)
        if checked and not self._ocr_toggle.isChecked():
            self._ocr_toggle.setChecked(True)

    def _do_capture(self):
        ocr = self._ocr_toggle.isChecked()
        translate = self._translate_toggle.isChecked()
        lang = self._lang_combo.currentText()

        if translate and ocr:
            mode = "ocr+translate"
        elif ocr:
            mode = "ocr"
        else:
            mode = "screenshot"

        self.capture_requested.emit(mode, lang)
