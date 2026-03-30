# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None
project_dir = Path(SPECPATH).parent

a = Analysis(
    [str(project_dir / 'src' / 'main.py')],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        (str(project_dir / 'resources' / 'icons'), 'resources/icons'),
    ],
    hiddenimports=[
        'PySide6.QtSvg',
        'src',
        'src.main',
        'src.config',
        'src.constants',
        'src.models',
        'src.services',
        'src.services.openai_service',
        'src.services.pdf_service',
        'src.services.image_service',
        'src.services.screen_capture',
        'src.workers',
        'src.workers.ocr_worker',
        'src.workers.translate_worker',
        'src.workers.batch_worker',
        'src.ui',
        'src.ui.main_window',
        'src.ui.system_tray',
        'src.ui.capture_overlay',
        'src.ui.capture_result_widget',
        'src.ui.styles',
        'src.ui.tabs',
        'src.ui.tabs.capture_tab',
        'src.ui.tabs.documents_tab',
        'src.ui.tabs.batch_tab',
        'src.ui.tabs.settings_tab',
        'src.ui.widgets',
        'src.ui.widgets.drop_zone',
        'src.ui.widgets.page_thumbnail_list',
        'src.ui.widgets.page_viewer',
        'src.ui.widgets.text_panel',
        'src.utils',
        'src.utils.hotkey',
        'src.utils.single_instance',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OCRStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(project_dir / 'resources' / 'icons' / 'app.ico') if (project_dir / 'resources' / 'icons' / 'app.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OCRStudio',
)
