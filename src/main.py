import signal
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from src.constants import APP_NAME, ORG_NAME
from src.utils.single_instance import ensure_single_instance


def main():
    mutex = ensure_single_instance("OCRStudioMutex")
    if mutex is None:
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)

    # Allow Ctrl+C to kill the app — Qt blocks SIGINT by default
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    # Fallback: periodic Python check so signal is delivered
    _timer = QTimer()
    _timer.timeout.connect(lambda: None)
    _timer.start(200)

    from src.config import ConfigManager
    config = ConfigManager()

    from src.ui.styles import LIGHT_THEME, DARK_THEME
    theme = str(config.get("general/theme", "light"))
    app.setStyleSheet(DARK_THEME if theme == "dark" else LIGHT_THEME)

    from src.ui.main_window import MainWindow
    window = MainWindow(config)

    from src.ui.system_tray import SystemTrayIcon
    tray = SystemTrayIcon(window, config)
    tray.show()

    # Global hotkey
    from src.utils.hotkey import GlobalHotkey
    hotkey = GlobalHotkey(config.get_hotkey())
    hotkey.triggered.connect(window.start_screen_capture)
    hotkey.start()

    # Re-register hotkey when settings change (connected via main window)
    def on_settings_changed():
        hotkey.update_hotkey(config.get_hotkey())

    # Store callback so main_window can call it after settings_tab is created
    window._hotkey_settings_callback = on_settings_changed

    start_minimized = config.get("general/start_minimized")
    if start_minimized == "true" or start_minimized is True:
        window.hide()
    else:
        window.show()

    exit_code = app.exec()
    hotkey.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
