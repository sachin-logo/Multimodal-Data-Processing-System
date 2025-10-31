# Multimodal Data Processing System

Ingest documents, images, audio/video, and YouTube links, then ask natural-language questions powered by Gemini. Includes a Streamlit UI and a simple CLI.

## Features
- Text extraction: PDF, DOCX, PPTX, TXT/MD
- Image OCR (optional): PNG/JPG/JPEG via Tesseract
- Audio/Video transcription: MP3/WAV/M4A/MP4 (ffmpeg recommended)
- YouTube: transcript retrieval with robust fallbacks
- Local SQLite storage for ingested content and search
- LLM answering via Google Gemini (1.5 family); image Q&A supported
- UI: Streamlit app; CLI: `main.py`

## Requirements
- Windows, macOS, or Linux
- Python 3.10+
- Google Gemini API key: set `GEMINI_API_KEY`
- Optional for certain features:
  - Tesseract OCR (image OCR)
  - ffmpeg + ffprobe (audio/video)

A Python virtual environment (`venv/`) is already present in this copy. You can reuse it or create your own.

## Setup

### 1) Activate venv
- PowerShell:
```powershell
cd "C:\Users\sachi\OneDrive\Desktop\multimedia"
.\venv\Scripts\Activate.ps1
```
- Command Prompt (cmd):
```bat
cd C:\Users\sachi\OneDrive\Desktop\multimedia
venv\Scripts\activate
```

### 2) Install dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Set your Gemini key
- PowerShell:
```powershell
$env:GEMINI_API_KEY="YOUR_KEY_HERE"
```
- Command Prompt (cmd):
```bat
set "GEMINI_API_KEY=YOUR_KEY_HERE"
```

## Run

### Streamlit UI (recommended)
```bash
streamlit run ui/streamlit_app.py
```
Then open the browser link. In the sidebar, upload a file or paste a YouTube URL. Use “Ask a Question” or “Ask about an Image”.

### CLI app
```bash
python main.py
```
Follow the menu to ingest content and ask questions.

## Optional tools

### Tesseract (image OCR)
Image Q&A works without OCR (multimodal). OCR is used during image ingestion only if installed.
- Winget (Admin PowerShell):
```powershell
winget install --id UB-Mannheim.TesseractOCR -e --accept-package-agreements --accept-source-agreements
```
- Or download from “UB Mannheim Tesseract OCR” wiki and install.
- If not on PATH, set (cmd example):
```bat
setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"
```
Open a new terminal after `setx`.

### ffmpeg (audio/video)
Recommended for audio/video conversions (MP3/MP4 → WAV).
- Chocolatey (Admin PowerShell):
```powershell
choco install ffmpeg -y
```
- If not on PATH, set (PowerShell example):
```powershell
$env:FFMPEG_BINARY="C:\path\to\ffmpeg.exe"
$env:FFPROBE_BINARY="C:\path\to\ffprobe.exe"
```

## Usage tips
- Supported inputs: `pdf, docx, pptx, txt, md, png, jpg/jpeg, mp3, wav, m4a, mp4, YouTube URL`
- Data is stored in `multimedia.db` (SQLite). It’s created on first run.
- Image Q&A: uploads the image and asks Gemini directly. OCR is disabled by default in the UI.

## Troubleshooting
- Missing GEMINI_API_KEY:
  - The app will show an error and stop. Set the variable as shown above and run again.
- Tesseract not found:
  - For ingestion OCR only. Install Tesseract and set `TESSERACT_CMD` if needed.
- Chocolatey lock/permission errors:
  - Close other package managers, run PowerShell as Administrator, remove stale locks from `C:\ProgramData\chocolatey\lib*`, then retry install.
- Streamlit deprecation warning for image sizing:
  - Addressed by using `use_container_width=True`.

## Project structure
```
multimedia/
  db/
    db_interface.py           # SQLite tables and queries
  extractors/
    text_extractors.py        # PDF, DOCX, PPTX, TXT/MD
    image_extractors.py       # OCR via pytesseract (optional)
    av_extractors.py          # Audio/video + YouTube helpers
  llm/
    gemini_interface.py       # Gemini wrapper (text + image Q&A)
  ui/
    streamlit_app.py          # Streamlit UI
  main.py                     # CLI entry point
  requirements.txt
  multimedia.db               # SQLite DB (created at runtime)
```

## Contributing
PRs welcome. Please follow existing style and keep code readable.

## License
Add your preferred license (e.g., MIT) here.
