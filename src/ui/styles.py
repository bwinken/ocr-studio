"""Light & Dark themes — NotebookLM-inspired, pill buttons, Material 3."""

_FONT = '"AR HuaLiT", "文鼎花栗體", "Microsoft JhengHei", "Arial", "Helvetica Neue", sans-serif'

# ─────────────────── Shared (non-color) rules ───────────────────
_SHARED = f"""
QMainWindow, QWidget {{
    font-family: {_FONT};
    font-size: 14px;
}}
QPushButton {{
    border-radius: 20px;
    padding: 8px 24px;
    font-weight: 500;
    font-size: 14px;
    border: none;
    margin: 1px 0 1px 0;
}}
QPushButton:pressed {{
    padding: 9px 24px 7px 24px;
    margin: 2px 0 0 0;
}}
QPushButton#winMin, QPushButton#winMax, QPushButton#winClose {{
    background: transparent;
    border: none;
    border-radius: 0;
    font-size: 14px;
    font-weight: 400;
    padding: 0;
}}
QLineEdit, QTextEdit, QPlainTextEdit {{
    border-radius: 12px;
    padding: 9px 14px;
    font-size: 13px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    padding: 8px 13px;
}}
QComboBox {{
    border-radius: 12px;
    padding: 8px 14px;
    min-width: 80px;
    font-size: 13px;
}}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow {{ image: none; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border-width: 2px; border-style: solid; }}
QLabel#appName {{ font-size: 14px; font-weight: 600; }}
QLabel#navSep {{ font-size: 14px; padding: 0 6px; }}
QLabel#navPage {{ font-size: 13px; font-weight: 500; }}
QLabel#connDot {{ font-size: 8px; padding: 0; min-width: 10px; }}
QLabel#connModel {{ font-size: 11px; padding: 0 14px 0 4px; }}
QLabel[heading="true"] {{ font-size: 18px; font-weight: 600; }}
QLabel[subheading="true"] {{ font-size: 13px; }}
QLabel[dimmed="true"] {{ font-size: 13px; }}
QGroupBox {{
    border-radius: 12px;
    margin-top: 14px;
    padding: 16px;
    padding-top: 24px;
    font-weight: 500;
    font-size: 13px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 3px 12px;
    font-weight: 600;
}}
QProgressBar {{ border: none; border-radius: 3px; height: 4px; text-align: center; }}
QProgressBar::chunk {{ border-radius: 3px; }}
QScrollBar:vertical {{ background-color: transparent; width: 6px; border: none; margin: 2px; }}
QScrollBar::handle:vertical {{ border-radius: 3px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background-color: transparent; height: 6px; border: none; margin: 2px; }}
QScrollBar::handle:horizontal {{ border-radius: 3px; min-width: 30px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QTabBar::tab {{ padding: 10px 22px; border: none; border-bottom: 2px solid transparent; font-weight: 500; }}
QListWidget {{ border-radius: 12px; padding: 4px; outline: none; }}
QListWidget::item {{ padding: 8px 10px; border-radius: 8px; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}
QDoubleSpinBox, QSpinBox {{ border-radius: 12px; padding: 6px 10px; }}
QToolTip {{ border: none; padding: 8px 12px; border-radius: 8px; font-size: 12px; }}
QPushButton#actionCard {{ border-radius: 12px; padding: 20px; text-align: left; }}
QWidget#titleBar {{ border-bottom-width: 1px; border-bottom-style: solid; }}
QWidget#statusBar {{ border-top-width: 1px; border-top-style: solid; }}
QWidget#docToolbar {{ border-bottom-width: 1px; border-bottom-style: solid; }}
"""

# ─────────────────── LIGHT THEME ───────────────────
LIGHT_THEME = _SHARED + """
/* Surface */
QMainWindow, QWidget { background-color: #F9F9FB; color: #1F1F1F; }

/* Title bar */
QWidget#titleBar { background-color: #FFFFFF; border-bottom-color: #EBEBEF; }
QLabel#appName { color: #1F1F1F; }
QLabel#navSep { color: #C4C4D0; }
QLabel#navPage { color: #8181A5; }
QLabel#connModel { color: #8181A5; }
QPushButton#winMin, QPushButton#winMax, QPushButton#winClose { color: #8181A5; }
QPushButton#winMin:hover, QPushButton#winMax:hover { background-color: #F0F0F5; }
QPushButton#winClose:hover { background-color: #D93025; color: #FFFFFF; }

/* Buttons */
QPushButton { background-color: #0B28D3; color: #FFFFFF; }
QPushButton:hover { background-color: #0920B0; }
QPushButton:pressed { background-color: #051570; }
QPushButton:disabled { background-color: #EBEBEF; color: #ADADC0; }
QPushButton[secondary="true"] { background-color: transparent; color: #0B28D3; border: 1px solid #DDDDE5; border-radius: 20px; }
QPushButton[secondary="true"]:hover { background-color: #F0F0F5; border-color: #0B28D3; border-radius: 20px; }
QPushButton[secondary="true"]:pressed { background-color: #E0E0EA; border-color: #071A8F; border-radius: 20px; }
QPushButton[secondary="true"]:disabled { color: #ADADC0; border-color: #EBEBEF; background: transparent; border-radius: 20px; }
QPushButton[danger="true"] { background-color: #D93025; color: #FFFFFF; border-radius: 20px; }
QPushButton[danger="true"]:pressed { background-color: #A52714; border-radius: 20px; }
QPushButton[success="true"] { background-color: #006F0C; color: #FFFFFF; border-radius: 20px; }
QPushButton[success="true"]:hover { background-color: #005A09; border-radius: 20px; }
QPushButton[success="true"]:pressed { background-color: #004506; border-radius: 20px; }
QPushButton[success="true"]:disabled { background-color: #EBEBEF; color: #ADADC0; border-radius: 20px; }

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit { background-color: #FFFFFF; color: #1F1F1F; border: 1px solid #DDDDE5; selection-background-color: #D2DAF8; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border: 2px solid #0B28D3; }
QComboBox { background-color: #FFFFFF; color: #1F1F1F; border: 1px solid #DDDDE5; }
QComboBox QAbstractItemView { background-color: #FFFFFF; color: #1F1F1F; border: 1px solid #EBEBEF; selection-background-color: #E8ECFB; }
QCheckBox { color: #1F1F1F; }
QCheckBox::indicator { border-color: #8181A5; background-color: #FFFFFF; }
QCheckBox::indicator:checked { background-color: #0B28D3; border-color: #0B28D3; }

/* Labels */
QLabel { color: #1F1F1F; }
QLabel[subheading="true"] { color: #8181A5; }
QLabel[dimmed="true"] { color: #ADADC0; }

/* Groups */
QGroupBox { border: 1px solid #EBEBEF; background-color: #FFFFFF; }
QGroupBox::title { color: #0B28D3; }

/* Progress */
QProgressBar { background-color: #EBEBEF; }
QProgressBar::chunk { background-color: #0B28D3; }

/* Scroll */
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background-color: #DDDDE5; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background-color: #ADADC0; }

/* Tabs */
QTabWidget::pane { border: 1px solid #EBEBEF; background-color: #FFFFFF; }
QTabBar::tab { background-color: transparent; color: #8181A5; }
QTabBar::tab:selected { color: #0B28D3; border-bottom-color: #0B28D3; }
QTabBar::tab:hover:!selected { color: #1F1F1F; background-color: #F0F0F5; }

/* Lists */
QListWidget { background-color: #FFFFFF; border: 1px solid #EBEBEF; }
QListWidget::item:selected { background-color: #E8ECFB; color: #1F1F1F; }
QListWidget::item:hover:!selected { background-color: #F5F5FA; }

/* Splitter */
QSplitter::handle { background-color: #EBEBEF; }

/* Misc */
QDoubleSpinBox, QSpinBox { background-color: #FFFFFF; color: #1F1F1F; border: 1px solid #DDDDE5; }
QToolTip { background-color: #2D2D2D; color: #F0F0F5; }
QWidget#statusBar { background-color: #FFFFFF; border-top-color: #EBEBEF; }
QPushButton#actionCard { background-color: #FFFFFF; border: 1px solid #EBEBEF; border-radius: 12px; margin: 0; }
QPushButton#actionCard:hover { border-color: #D2DAF8; background-color: #FAFAFD; border-radius: 12px; }
QPushButton#actionCard:pressed { background-color: #E8E8F0; border-color: #0B28D3; border-radius: 12px; padding-top: 22px; padding-bottom: 18px; }
QWidget#docToolbar { background-color: #FFFFFF; border-bottom-color: #EBEBEF; }

/* Theme-aware inline classes */
QLabel#textPrimary { color: #1F1F1F; }
QLabel#textSecondary { color: #8181A5; }
QLabel#textDimmed { color: #ADADC0; }
QLabel#textAccent { color: #0B28D3; }
QWidget#bannerBg { background-color: #F0F2FF; border-radius: 12px; }
QWidget#surfaceAlt { background-color: #F0F0F5; border-radius: 12px; }
QWidget#dropInner { border: 2px dashed #D0D0DD; border-radius: 20px; background-color: #FAFAFD; }
QWidget#dropInnerHover { border: 3px dashed #0B28D3; border-radius: 20px; background-color: #EEF0FF; }

/* Sidebar */
QPushButton#sidebarBtn { font-size: 20px; border-radius: 12px; padding: 0; border: none; background: transparent; color: #5F5F8A; }
QPushButton#sidebarBtn:hover { background-color: #EBEBEF; color: #0B28D3; }
QLabel#sidebarGrip { font-size: 16px; color: #ADADC0; background: transparent; border-bottom: 1px solid #EBEBEF; border-radius: 0; }
"""

# ─────────────────── DARK THEME ───────────────────
DARK_THEME = _SHARED + """
/* Surface */
QMainWindow, QWidget { background-color: #1A1A2E; color: #E0E0F0; }

/* Title bar */
QWidget#titleBar { background-color: #16162A; border-bottom-color: #2A2A45; }
QLabel#appName { color: #E0E0F0; }
QLabel#navSep { color: #4A4A6A; }
QLabel#navPage { color: #8181A5; }
QLabel#connModel { color: #8181A5; }
QPushButton#winMin, QPushButton#winMax, QPushButton#winClose { color: #8181A5; }
QPushButton#winMin:hover, QPushButton#winMax:hover { background-color: #2A2A45; }
QPushButton#winClose:hover { background-color: #D93025; color: #FFFFFF; }

/* Buttons */
QPushButton { background-color: #3D5AFE; color: #FFFFFF; }
QPushButton:hover { background-color: #304FFE; }
QPushButton:pressed { background-color: #1A33CC; }
QPushButton:disabled { background-color: #2A2A45; color: #5A5A7A; }
QPushButton[secondary="true"] { background-color: transparent; color: #7B8CFF; border: 1px solid #2A2A45; border-radius: 20px; }
QPushButton[secondary="true"]:hover { background-color: #22223A; border-color: #7B8CFF; border-radius: 20px; }
QPushButton[secondary="true"]:pressed { background-color: #1A1A30; border-color: #3D5AFE; border-radius: 20px; }
QPushButton[secondary="true"]:disabled { color: #5A5A7A; border-color: #2A2A45; background: transparent; border-radius: 20px; }
QPushButton[danger="true"] { background-color: #D93025; color: #FFFFFF; border-radius: 20px; }
QPushButton[danger="true"]:pressed { background-color: #A52714; border-radius: 20px; }
QPushButton[success="true"] { background-color: #00C853; color: #1A1A2E; border-radius: 20px; }
QPushButton[success="true"]:hover { background-color: #00E676; border-radius: 20px; }
QPushButton[success="true"]:pressed { background-color: #009624; border-radius: 20px; }
QPushButton[success="true"]:disabled { background-color: #2A2A45; color: #5A5A7A; border-radius: 20px; }

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit { background-color: #22223A; color: #E0E0F0; border: 1px solid #2A2A45; selection-background-color: #3D5AFE40; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border: 2px solid #3D5AFE; }
QComboBox { background-color: #22223A; color: #E0E0F0; border: 1px solid #2A2A45; }
QComboBox QAbstractItemView { background-color: #22223A; color: #E0E0F0; border: 1px solid #2A2A45; selection-background-color: #3D5AFE30; }
QCheckBox { color: #E0E0F0; }
QCheckBox::indicator { border-color: #5A5A7A; background-color: #22223A; }
QCheckBox::indicator:checked { background-color: #3D5AFE; border-color: #3D5AFE; }

/* Labels */
QLabel { color: #E0E0F0; }
QLabel[subheading="true"] { color: #8181A5; }
QLabel[dimmed="true"] { color: #5A5A7A; }

/* Groups */
QGroupBox { border: 1px solid #2A2A45; background-color: #1E1E35; }
QGroupBox::title { color: #7B8CFF; }

/* Progress */
QProgressBar { background-color: #2A2A45; }
QProgressBar::chunk { background-color: #3D5AFE; }

/* Scroll */
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background-color: #3A3A55; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background-color: #5A5A7A; }

/* Tabs */
QTabWidget::pane { border: 1px solid #2A2A45; background-color: #1E1E35; }
QTabBar::tab { background-color: transparent; color: #8181A5; }
QTabBar::tab:selected { color: #7B8CFF; border-bottom-color: #3D5AFE; }
QTabBar::tab:hover:!selected { color: #E0E0F0; background-color: #22223A; }

/* Lists */
QListWidget { background-color: #1E1E35; border: 1px solid #2A2A45; }
QListWidget::item:selected { background-color: #3D5AFE20; color: #E0E0F0; }
QListWidget::item:hover:!selected { background-color: #22223A; }

/* Splitter */
QSplitter::handle { background-color: #2A2A45; }

/* Misc */
QDoubleSpinBox, QSpinBox { background-color: #22223A; color: #E0E0F0; border: 1px solid #2A2A45; }
QToolTip { background-color: #E0E0F0; color: #1A1A2E; }
QWidget#statusBar { background-color: #16162A; border-top-color: #2A2A45; }
QPushButton#actionCard { background-color: #1E1E35; border: 1px solid #2A2A45; border-radius: 12px; margin: 0; }
QPushButton#actionCard:hover { border-color: #3D5AFE40; background-color: #22223A; border-radius: 12px; }
QPushButton#actionCard:pressed { background-color: #16162A; border-color: #3D5AFE; border-radius: 12px; padding-top: 22px; padding-bottom: 18px; }
QWidget#docToolbar { background-color: #16162A; border-bottom-color: #2A2A45; }

/* Theme-aware inline classes */
QLabel#textPrimary { color: #E0E0F0; }
QLabel#textSecondary { color: #8181A5; }
QLabel#textDimmed { color: #5A5A7A; }
QLabel#textAccent { color: #7B8CFF; }
QWidget#bannerBg { background-color: #22224A; border-radius: 12px; }
QWidget#surfaceAlt { background-color: #22223A; border-radius: 12px; }
QWidget#dropInner { border: 2px dashed #3A3A55; border-radius: 20px; background-color: #1E1E35; }
QWidget#dropInnerHover { border: 3px dashed #3D5AFE; border-radius: 20px; background-color: #22224A; }

/* Sidebar */
QPushButton#sidebarBtn { font-size: 20px; border-radius: 12px; padding: 0; border: none; background: transparent; color: #8181A5; }
QPushButton#sidebarBtn:hover { background-color: #2A2A45; color: #7B8CFF; }
QLabel#sidebarGrip { font-size: 16px; color: #5A5A7A; background: transparent; border-bottom: 1px solid #2A2A45; border-radius: 0; }
"""
