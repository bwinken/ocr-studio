"""Home page — NotebookLM-style clean cards with indigo accents."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.constants import UI

# NotebookLM-style accent palette
_ACCENTS = {
    "indigo": "#0B28D3",
    "violet": "#7B1FA2",
    "amber": "#E8710A",
    "teal": "#00897B",
}


class ActionCard(QPushButton):
    """Clean card with colored left accent bar — NotebookLM style."""

    def __init__(self, title: str, description: str, accent: str, badge: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("actionCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(110)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 20, 0)
        outer.setSpacing(0)

        # Left accent bar
        bar = QWidget()
        bar.setFixedWidth(4)
        bar.setStyleSheet(f"background: {accent}; border-radius: 2px;")
        outer.addWidget(bar)

        content = QVBoxLayout()
        content.setContentsMargins(18, 16, 0, 16)
        content.setSpacing(6)

        # Title row
        row = QHBoxLayout()
        row.setSpacing(10)

        t = QLabel(title)
        t.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #1F1F1F; "
            "background: transparent; border: none;"
        )
        t.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(t)

        if badge:
            b = QLabel(badge)
            b.setStyleSheet(
                f"font-size: 10px; color: {accent}; background-color: #F0F0F5; "
                "border: none; border-radius: 8px; padding: 2px 8px;"
            )
            b.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            row.addWidget(b)

        row.addStretch()
        content.addLayout(row)

        d = QLabel(description)
        d.setWordWrap(True)
        d.setStyleSheet(
            "font-size: 12px; color: #8181A5; background: transparent; "
            "border: none; line-height: 1.4;"
        )
        d.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        content.addWidget(d)

        content.addStretch()
        outer.addLayout(content, 1)


class HomePage(QWidget):
    capture_clicked = Signal()
    document_clicked = Signal()
    batch_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(52, 40, 52, 40)
        layout.setSpacing(0)

        title = QLabel("選擇功能")
        title.setStyleSheet("font-size: 24px; font-weight: 400; color: #1F1F1F;")
        layout.addWidget(title)

        hotkey = str(self._config.get_hotkey())
        hint = QLabel(f"使用 {hotkey} 快速截圖 OCR")
        hint.setStyleSheet("font-size: 13px; color: #8181A5; margin-top: 4px;")
        layout.addWidget(hint)

        layout.addSpacing(28)

        grid = QGridLayout()
        grid.setSpacing(12)

        cards = [
            (UI["capture_title"], UI["capture_desc"], _ACCENTS["indigo"], hotkey, self.capture_clicked),
            (UI["document_title"], UI["document_desc"], _ACCENTS["violet"], "", self.document_clicked),
            (UI["batch_title"], UI["batch_desc"], _ACCENTS["amber"], "", self.batch_clicked),
            (UI["settings_title"], UI["settings_desc"], _ACCENTS["teal"], "", self.settings_clicked),
        ]

        for i, (title, desc, accent, badge, signal) in enumerate(cards):
            card = ActionCard(title, desc, accent, badge)
            card.clicked.connect(signal.emit)
            grid.addWidget(card, i // 2, i % 2)

        layout.addLayout(grid, 1)
