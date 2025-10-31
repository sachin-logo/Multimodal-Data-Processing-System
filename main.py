"""
Multimodal Data Processing System
Entrypoint for ingestion, processing, and question-answering
"""

import os
import sys
from extractors.text_extractors import extract_pdf_text, extract_docx_text, extract_pptx_text, extract_txt_md
from extractors.image_extractors import extract_image_text
from extractors.av_extractors import extract_audio_text, extract_video_text, extract_youtube_text
from db.db_interface import init_db, insert_file, insert_text, search_text, get_recent_contents
from llm.gemini_interface import GeminiWrapper

# 1. Setup DB
init_db()

# 2. Load Gemini API key from env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    print("[ERROR] Please set GEMINI_API_KEY environment variable.")
    sys.exit(1)
gemini = GeminiWrapper(GEMINI_API_KEY)

# 3. File ingestion
SUPPORTED_TYPES = ['pdf','docx','pptx','txt','md','png','jpg','mp3','mp4','youtube']
def ingest(path_or_url):
    ext = os.path.splitext(path_or_url)[-1].lower().replace('.','')
    if path_or_url.startswith("http") and ('youtube' in path_or_url or 'youtu.be' in path_or_url):
        ftype = 'youtube'
        content = extract_youtube_text(path_or_url)
        if not content:
            print("[WARN] Could not retrieve YouTube transcript; attempted audio transcription fallback.")
    elif ext in ['pdf', 'docx', 'pptx', 'txt', 'md']:
        ftype = ext
        if ext=='pdf': content = extract_pdf_text(path_or_url)
        elif ext=='docx': content = extract_docx_text(path_or_url)
        elif ext=='pptx': content = extract_pptx_text(path_or_url)
        else: content = extract_txt_md(path_or_url)
    elif ext in ['png','jpg']:
        ftype = 'image'
        content = extract_image_text(path_or_url)
    elif ext == 'mp3':
        ftype = 'audio'
        try:
            content = extract_audio_text(path_or_url)
        except Exception as e:
            print(f"[ERROR] Audio transcription failed: {e}")
            content = ""
    elif ext == 'mp4':
        ftype = 'video'
        try:
            content = extract_video_text(path_or_url)
        except Exception as e:
            print(f"[ERROR] Video transcription failed: {e}")
            content = ""
    else:
        print("Unsupported file type.")
        return
    file_id = insert_file(path_or_url, ftype)
    insert_text(file_id, content or "")
    print(f"[INFO] Ingested {path_or_url}")

# 4. Query loop
def answer_query(question):
    # Retrieve top matches
    results = search_text(question)
    if results:
        context = '\n----\n'.join([c for _, c in results])
    else:
        # Fallback: use the most recently ingested content
        recent = get_recent_contents(limit=1)
        if recent:
            context = recent[0][1]
            print(f"[INFO] Using recent file as context: {recent[0][0]}")
        else:
            context = None
    response = gemini.answer(question, context)
    print("\n== Answer ==\n", response)

if __name__ == "__main__":
    print('Multimodal Data Processing System')
    print('1. Ingest file or YouTube url')
    print('2. Ask a question')
    print('3. Exit')
    while True:
        cmd = input('Select option: ').strip()
        if cmd == '1':
            path = input('Enter file path or YouTube url: ').strip()
            ingest(path)
        elif cmd == '2':
            q = input('Enter your question: ')
            answer_query(q)
        elif cmd == '3':
            break
        else:
            print('Invalid choice.')
