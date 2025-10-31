import os
import sys
import tempfile
import streamlit as st

# Ensure project root is on sys.path when running from ui/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from extractors.text_extractors import (
    extract_pdf_text,
    extract_docx_text,
    extract_pptx_text,
    extract_txt_md,
)
from extractors.image_extractors import extract_image_text
from extractors.av_extractors import extract_audio_text, extract_video_text, extract_youtube_text
from db.db_interface import init_db, insert_file, insert_text, search_text, get_recent_contents
from llm.gemini_interface import GeminiWrapper


def get_gemini():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        st.error("GEMINI_API_KEY environment variable not set.")
        st.stop()
    return GeminiWrapper(api_key)


def save_uploaded_file(uploaded_file) -> str:
    suffix = os.path.splitext(uploaded_file.name)[-1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.getbuffer())
    tmp.flush()
    tmp.close()
    return tmp.name


def ingest_path_or_url(path_or_url: str):
    ext = os.path.splitext(path_or_url)[-1].lower().replace('.', '')
    if path_or_url.startswith("http") and ("youtube" in path_or_url or "youtu.be" in path_or_url):
        ftype = 'youtube'
        content = extract_youtube_text(path_or_url)
        if not content:
            st.warning("Could not retrieve YouTube transcript; tried audio/metadata fallback.")
    elif ext in ['pdf', 'docx', 'pptx', 'txt', 'md']:
        ftype = ext
        if ext == 'pdf':
            content = extract_pdf_text(path_or_url)
        elif ext == 'docx':
            content = extract_docx_text(path_or_url)
        elif ext == 'pptx':
            content = extract_pptx_text(path_or_url)
        else:
            content = extract_txt_md(path_or_url)
    elif ext in ['png', 'jpg', 'jpeg']:
        ftype = 'image'
        try:
            content = extract_image_text(path_or_url)
        except Exception as e:
            st.error(f"Image OCR failed: {e}. If on Windows, install Tesseract and/or set TESSERACT_CMD to tesseract.exe.")
            content = ""
    elif ext in ['mp3', 'wav', 'm4a']:
        ftype = 'audio'
        try:
            content = extract_audio_text(path_or_url)
        except Exception as e:
            st.error(f"Audio transcription failed: {e}")
            content = ""
    elif ext == 'mp4':
        ftype = 'video'
        try:
            content = extract_video_text(path_or_url)
        except Exception as e:
            st.error(f"Video transcription failed: {e}")
            content = ""
    else:
        st.error("Unsupported file type.")
        return

    file_id = insert_file(path_or_url, ftype)
    insert_text(file_id, content or "")
    st.success(f"Ingested: {path_or_url}")


def answer_query(question: str, gemini: GeminiWrapper):
    results = search_text(question)
    source = None
    if results:
        context = '\n----\n'.join([c for _, c in results])
        # pick first source path for display
        source = results[0][0]
    else:
        recent = get_recent_contents(limit=1)
        if recent:
            source = recent[0][0]
            context = recent[0][1]
        else:
            context = None
    answer = gemini.answer(question, context)
    return answer, source, (context[:400] + '...') if context and len(context) > 400 else context


def main():
    st.set_page_config(page_title="Multimodal Data Processing System", page_icon="🧠", layout="wide")

    # ---------- Header ----------
    st.title("🧠 Multimodal Data Processing System")
    st.caption("Ingest files and videos, then ask natural-language questions powered by Gemini.")
    init_db()
    gemini = get_gemini()

    with st.sidebar:
        st.header("Ingest")
        uploaded = st.file_uploader("Upload a file", type=[
            'pdf','docx','pptx','txt','md','png','jpg','jpeg','mp3','wav','m4a','mp4'
        ])
        url = st.text_input("Or YouTube URL")
        if st.button("Ingest"):
            if uploaded is not None:
                path = save_uploaded_file(uploaded)
                ingest_path_or_url(path)
            elif url:
                ingest_path_or_url(url)
            else:
                st.warning("Provide a file or URL to ingest.")

    st.header("Ask a Question")
    q = st.text_input("Your question")
    if st.button("Get Answer"):
        if not q.strip():
            st.warning("Enter a question.")
        else:
            ans, src, ctx_preview = answer_query(q, gemini)
            st.subheader("Answer")
            if not ans:
                st.warning("No answer was generated. Try a more specific question or ingest more content.")
            elif isinstance(ans, str) and ans.lower().startswith("llm error:"):
                st.error(ans)
            else:
                st.write(ans)
            if src or ctx_preview:
                with st.expander("Context used"):
                    if src:
                        st.caption(f"Source: {src}")
                    if ctx_preview:
                        st.text(ctx_preview)

    st.header("Ask about an Image")
    col1, col2 = st.columns([1, 2])
    with col1:
        image_file = st.file_uploader("Upload image for Q&A", type=['png','jpg','jpeg'])
        if image_file is not None:
            st.image(image_file, caption=image_file.name, use_container_width=True)
    with col2:
        img_q = st.text_input("Your question about this image")
        if st.button("Answer about image"):
            if image_file is None:
                st.warning("Please upload an image first.")
            elif not img_q.strip():
                st.warning("Enter a question about the image.")
            else:
                # Save to temp and optionally OCR for hint
                tmp_path = save_uploaded_file(image_file)
                # OCR is disabled by request; do not attempt OCR hints
                ocr_hint = None
                try:
                    answer = gemini.answer_about_image(tmp_path, img_q, ocr_hint=ocr_hint)
                except Exception as e:
                    answer = f"LLM error: {e}"
                st.subheader("Answer")
                if not answer:
                    st.warning("No answer was generated. Try a more specific question.")
                elif isinstance(answer, str) and answer.lower().startswith("llm error:"):
                    st.error(answer)
                else:
                    st.write(answer)


if __name__ == "__main__":
    main()


