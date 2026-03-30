from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from src.constants import UI


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, main_window, config):
        super().__init__(main_window)
        self.main_window = main_window
        self._config = config

        self._setup_icon()
        self._setup_menu()
        self.activated.connect(self._on_activated)

    def _setup_icon(self):
        icon = QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_ComputerIcon
        )
        self.setIcon(icon)
        self.setToolTip("OCR Studio")

    def _setup_menu(self):
        menu = QMenu()
        menu.addAction(UI["tray_capture"], self.main_window.start_screen_capture)
        menu.addAction(UI["tray_show"], self._show_window)
        menu.addSeparator()
        menu.addAction(UI["tray_settings"], self._open_settings)
        menu.addSeparator()
        menu.addAction(UI["tray_quit"], QApplication.instance().quit)
        self.setContextMenu(menu)

    def _show_window(self):
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def _open_settings(self):
        self._show_window()
        self.main_window._show_settings()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()
