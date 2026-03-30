"""NotebookLM-inspired light theme — Google Sans feel, pill buttons, Material 3."""

DARK_THEME = """
/* ── Surface ── */
QMainWindow, QWidget {
    background-color: #F9F9FB;
    color: #1F1F1F;
    font-family: "Segoe UI Variable", "Segoe UI", "Microsoft JhengHei UI", sans-serif;
    font-size: 13px;
}

/* ── Title Bar ── */
QWidget#titleBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #EBEBEF;
}
QLabel#appName {
    font-size: 14px;
    font-weight: 600;
    color: #1F1F1F;
}
QLabel#navSep {
    color: #C4C4D0;
    font-size: 14px;
    padding: 0 6px;
}
QLabel#navPage {
    color: #8181A5;
    font-size: 13px;
    font-weight: 500;
}
QLabel#connDot { font-size: 8px; padding: 0; min-width: 10px; }
QLabel#connModel {
    font-size: 11px;
    color: #8181A5;
    padding: 0 14px 0 4px;
}

/* Title bar window controls */
QPushButton#winMin, QPushButton#winMax, QPushButton#winClose {
    background: transparent;
    border: none;
    border-radius: 0;
    color: #8181A5;
    font-size: 14px;
    font-weight: 400;
    padding: 0;
}
QPushButton#winMin:hover, QPushButton#winMax:hover {
    background-color: #F0F0F5;
}
QPushButton#winClose:hover {
    background-color: #D93025;
    color: #FFFFFF;
}

/* ── Buttons — pill shape ── */
QPushButton {
    background-color: #0B28D3;
    color: #FFFFFF;
    border: none;
    border-radius: 20px;
    padding: 8px 24px;
    font-weight: 500;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #0920B0;
    /* Material shadow on hover */
}
QPushButton:pressed { background-color: #071A8F; }
QPushButton:disabled { background-color: #EBEBEF; color: #ADADC0; }

QPushButton[secondary="true"] {
    background-color: transparent;
    color: #0B28D3;
    border: 1px solid #DDDDE5;
    border-radius: 20px;
}
QPushButton[secondary="true"]:hover {
    background-color: #F0F0F5;
    border-color: #0B28D3;
}
QPushButton[secondary="true"]:disabled {
    color: #ADADC0;
    border-color: #EBEBEF;
    background: transparent;
}

QPushButton[danger="true"] { background-color: #D93025; color: #FFFFFF; }
QPushButton[danger="true"]:hover { background-color: #C5221F; }

QPushButton[success="true"] { background-color: #006F0C; color: #FFFFFF; }
QPushButton[success="true"]:hover { background-color: #005A09; }
QPushButton[success="true"]:disabled { background-color: #EBEBEF; color: #ADADC0; }

/* ── Inputs ── */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF;
    color: #1F1F1F;
    border: 1px solid #DDDDE5;
    border-radius: 12px;
    padding: 9px 14px;
    selection-background-color: #D2DAF8;
    selection-color: #1F1F1F;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #0B28D3;
    padding: 8px 13px;
}

QComboBox {
    background-color: #FFFFFF;
    color: #1F1F1F;
    border: 1px solid #DDDDE5;
    border-radius: 12px;
    padding: 8px 14px;
    min-width: 80px;
    font-size: 13px;
}
QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow { image: none; }
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #1F1F1F;
    border: 1px solid #EBEBEF;
    border-radius: 8px;
    selection-background-color: #E8ECFB;
    selection-color: #1F1F1F;
    outline: none;
    padding: 4px;
}

QCheckBox { spacing: 8px; color: #1F1F1F; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border-radius: 4px;
    border: 2px solid #8181A5;
    background-color: #FFFFFF;
}
QCheckBox::indicator:checked { background-color: #0B28D3; border-color: #0B28D3; }

/* ── Labels ── */
QLabel { color: #1F1F1F; }
QLabel[heading="true"] { font-size: 16px; font-weight: 600; }
QLabel[subheading="true"] { font-size: 12px; color: #8181A5; }
QLabel[dimmed="true"] { color: #ADADC0; font-size: 12px; }

/* ── Groups ── */
QGroupBox {
    border: 1px solid #EBEBEF;
    border-radius: 12px;
    margin-top: 14px;
    padding: 16px;
    padding-top: 24px;
    font-weight: 500;
    font-size: 13px;
    background-color: #FFFFFF;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 3px 12px;
    color: #0B28D3;
    font-weight: 600;
}

/* ── Progress ── */
QProgressBar {
    border: none;
    border-radius: 3px;
    background-color: #EBEBEF;
    height: 4px;
    text-align: center;
}
QProgressBar::chunk { background-color: #0B28D3; border-radius: 3px; }

/* ── Scroll ── */
QScrollBar:vertical {
    background-color: transparent;
    width: 6px;
    border: none;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background-color: #DDDDE5;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background-color: #ADADC0; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background-color: transparent;
    height: 6px;
    border: none;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background-color: #DDDDE5;
    border-radius: 3px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background-color: #ADADC0; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Tabs ── */
QTabWidget::pane { border: 1px solid #EBEBEF; background-color: #FFFFFF; }
QTabBar::tab {
    background-color: transparent;
    color: #8181A5;
    padding: 10px 22px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 500;
}
QTabBar::tab:selected { color: #0B28D3; border-bottom: 2px solid #0B28D3; }
QTabBar::tab:hover:!selected { color: #1F1F1F; background-color: #F0F0F5; }

/* ── Lists ── */
QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #EBEBEF;
    border-radius: 12px;
    padding: 4px;
    outline: none;
}
QListWidget::item { padding: 8px 10px; border-radius: 8px; }
QListWidget::item:selected { background-color: #E8ECFB; color: #1F1F1F; }
QListWidget::item:hover:!selected { background-color: #F5F5FA; }

/* ── Splitter ── */
QSplitter::handle { background-color: #EBEBEF; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }

/* ── Misc ── */
QDoubleSpinBox, QSpinBox {
    background-color: #FFFFFF;
    color: #1F1F1F;
    border: 1px solid #DDDDE5;
    border-radius: 12px;
    padding: 6px 10px;
}
QToolTip {
    background-color: #2D2D2D;
    color: #F0F0F5;
    border: none;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 12px;
}

/* ── Status Bar ── */
QWidget#statusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #EBEBEF;
}

/* ── Home Action Cards ── */
QPushButton#actionCard {
    background-color: #FFFFFF;
    border: 1px solid #EBEBEF;
    border-radius: 12px;
    padding: 20px;
    text-align: left;
}
QPushButton#actionCard:hover {
    border-color: #D2DAF8;
    background-color: #FAFAFD;
    /* Subtle shadow — QSS doesn't support box-shadow natively */
}
QPushButton#actionCard:pressed {
    background-color: #F0F0F5;
}

/* ── Document Toolbar ── */
QWidget#docToolbar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #EBEBEF;
}

/* ── Form Rows ── */
QFormLayout {
    spacing: 8px;
}
"""
