# OCR Studio

Windows 桌面 OCR 辨識與翻譯工具。透過 AI 模型自動偵測文字位置、辨識內容並翻譯成多國語言。

## 下載安裝

1. 前往 [Releases](https://github.com/bwinken/ocr-studio/releases) 頁面
2. 下載最新版 `OCRStudio-vX.X.X-win64.zip`
3. 解壓縮到任意位置
4. 執行 `OCRStudio.exe`
5. 首次啟動會要求設定 API Key 和 Base URL

> 不需要安裝，不需要管理員權限。
>
> **注意**：首次執行時 Windows SmartScreen 可能顯示「無法辨識的應用程式」警告。
> 點擊「更多資訊」→「仍要執行」即可。這是因為程式尚未購買數位簽章憑證，不影響安全性。

## 功能

### 螢幕截圖 OCR

框選螢幕任意區域，自動辨識文字。首頁可切換三種模式：

| 模式 | OCR | 翻譯 | 複製到剪貼簿 |
|---|---|---|---|
| 純截圖 | - | - | 圖片 |
| OCR | O | - | 辨識文字 |
| OCR + 翻譯 | O | O | 翻譯結果 |

全域快捷鍵 `Ctrl+Shift+O` 可隨時截圖（可在設定中自訂）。

### 文件處理

- 拖放 PDF 或圖片到視窗
- 逐頁 OCR 辨識 + 翻譯
- 匯出 PDF（三種覆蓋模式）：
  - **翻譯覆蓋在原圖上** — 白底顯示翻譯文字
  - **隱藏文字層** — 透明文字（可搜尋、可複製）
  - **只保留翻譯文字** — 移除原圖，僅保留翻譯

### 批次處理

- 選擇輸入 / 輸出資料夾，一次處理所有文件
- 支援兩種輸出格式：
  - **原始格式** — PDF 輸出 PDF（帶文字覆蓋），圖片輸出 PNG
  - **純文字 TXT** — 只輸出辨識 / 翻譯文字（多頁 PDF 按頁分檔：`檔名_1.txt`、`檔名_2.txt`）

### 其他

- Dark / Light 主題切換
- 迷你工具列模式（收起為一排小 icon）
- 系統匣常駐

## 支援格式

PDF、PNG、JPG、JPEG、BMP、TIFF、WebP

## 支援 API

需要 OpenAI 相容的 API 端點。支援：

- **OpenAI** — GPT-4o、GPT-5.4-nano 等
- **PaddleOCR-VL-1.5** — 透過 vLLM 部署（模型名含 `paddle` 自動切換模式）
- **Qwen** — Qwen3.5-27B / 35B 等
- **其他** — 任何提供 `/v1/chat/completions` 的 OpenAI 相容 API（Ollama、vLLM、Azure 等）

可在設定中分別指定 OCR 端點和翻譯端點（不同模型、不同伺服器）。

## 翻譯語言

English、繁體中文、简体中文、日本語、한국어、Deutsch、Francais、Espanol

## 從原始碼執行

需要 Python 3.11+ 和 [uv](https://docs.astral.sh/uv/)：

```bash
git clone https://github.com/bwinken/ocr-studio.git
cd ocr-studio
uv sync
uv run python -m src.main
```

## 建置 exe

```bash
uv pip install pyinstaller
uv run python scripts/build_exe.py
```

輸出位於 `build/dist/OCRStudio/`。

## License

MIT
