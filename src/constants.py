APP_NAME = "OCR Studio"
APP_VERSION = "1.0.0"
ORG_NAME = "OCRStudio"

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS

TARGET_LANGUAGES = [
    "English",
    "繁體中文",
    "简体中文",
    "日本語",
    "한국어",
    "Deutsch",
    "Français",
    "Español",
]

DEFAULT_HOTKEY = "Ctrl+Shift+O"

# Chinese UI strings
UI = {
    "app_title": "OCR Studio",
    "ready": "就緒",
    "settings": "設定",
    "save": "儲存",
    "cancel": "取消",
    "close": "關閉",
    "copy": "複製",
    "export": "匯出",
    "browse": "瀏覽",
    "start": "開始處理",
    "stop": "停止",
    "test": "測試",

    # Setup
    "setup_title": "歡迎使用 OCR Studio",
    "setup_subtitle": "請先設定 OpenAI API 連線資訊",
    "api_key": "API Key",
    "api_key_placeholder": "sk-...",
    "base_url": "Base URL",
    "base_url_placeholder": "https://api.openai.com/v1",
    "test_connection": "測試連線",
    "test_success": "連線成功！",
    "test_fail": "連線失敗",
    "save_and_start": "儲存並開始使用",
    "no_api_key": "請先設定 API Key",

    # Home
    "home_title": "選擇功能",
    "capture_title": "截圖 OCR",
    "capture_desc": "框選螢幕區域，辨識文字並翻譯",
    "capture_hotkey": "快捷鍵：{hotkey}",
    "document_title": "文件處理",
    "document_desc": "開啟 PDF 或圖片，進行 OCR 辨識與翻譯",
    "batch_title": "批次處理",
    "batch_desc": "選擇資料夾，自動處理所有 PDF 與圖片",
    "settings_title": "設定",
    "settings_desc": "API 連線、語言、快捷鍵等設定",

    # Capture
    "capture_history": "截圖紀錄",
    "capture_hint": "按下快捷鍵 {hotkey} 來截取螢幕區域",
    "ocr_text": "辨識文字",
    "translated_text": "翻譯結果",
    "translate": "翻譯",
    "translating": "翻譯中...",
    "copy_ocr": "複製原文",
    "copy_translation": "複製翻譯",
    "auto_translate": "自動翻譯",
    "target_language": "目標語言",

    # Documents
    "documents_title": "文件處理",
    "open_file": "開啟檔案",
    "ocr_all": "全部 OCR",
    "translate_all": "全部翻譯",
    "export_pdf": "匯出 PDF",
    "drop_hint": "拖放 PDF 或圖片檔案到此處\n或點擊「開啟檔案」",
    "loading": "載入中...",
    "ocr_running": "OCR 辨識中...",
    "ocr_complete": "OCR 完成",
    "translate_running": "翻譯中...",
    "translate_complete": "翻譯完成",
    "export_complete": "匯出完成",
    "pages": "頁面",

    # Batch
    "batch_title": "批次處理",
    "input_folder": "輸入資料夾",
    "output_folder": "輸出資料夾",
    "overlay_mode": "覆蓋模式",
    "overlay_visible": "翻譯覆蓋在原圖上",
    "overlay_invisible": "隱藏文字層（可搜尋）",
    "overlay_replace": "只保留翻譯文字（移除原圖）",
    "do_translate": "翻譯文字",
    "processing": "處理中...",
    "batch_complete": "批次處理完成：{success} 成功，{failed} 失敗",

    # Settings
    "settings_api": "OpenAI API",
    "settings_general": "一般設定",
    "settings_capture": "截圖設定",
    "settings_startup": "啟動設定",
    "ocr_model": "OCR 模型",
    "translate_model": "翻譯模型",
    "default_language": "預設目標語言",
    "pdf_scale": "PDF 渲染倍率",
    "hotkey": "全域快捷鍵",
    "auto_translate_capture": "截圖後自動翻譯",
    "copy_to_clipboard": "辨識後自動複製",
    "start_minimized": "啟動時最小化到系統匣",
    "start_with_windows": "開機自動啟動",
    "settings_saved": "設定已儲存",

    # Tray
    "tray_capture": "截圖 OCR",
    "tray_show": "顯示視窗",
    "tray_settings": "設定",
    "tray_quit": "結束",
}
