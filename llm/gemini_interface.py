import google.generativeai as genai

class GeminiWrapper:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Robust model selection with live probe
        candidates = [
            'gemini-1.5-flash', 'gemini-1.5-flash-001', 'gemini-1.5-flash-8b', 'gemini-1.5-flash-8b-001',
            'gemini-1.5-pro', 'gemini-1.5-pro-001', 'gemini-pro', 'gemini-1.0-pro'
        ]
        # Also consider names returned by list_models (may already include 'models/' prefix)
        model_names = set()
        try:
            for m in genai.list_models():
                if getattr(m, 'supported_generation_methods', None) and 'generateContent' in m.supported_generation_methods:
                    model_names.add(m.name)
        except Exception:
            pass

        # Build a probe list with raw and prefixed variants
        probe_list = []
        for n in candidates:
            probe_list.append(n)
            probe_list.append(f'models/{n}')
        # Add discovered names from API
        probe_list.extend(list(model_names))

        self.model = None
        for name in probe_list:
            try:
                model = genai.GenerativeModel(name)
                # quick probe
                resp = model.generate_content("ping")
                _ = getattr(resp, 'text', '')
                self.model = model
                break
            except Exception:
                continue
        if self.model is None:
            # As a last resort, set to a common default (may still fail at call time)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def answer(self, prompt, context=None):
        # Trim context to keep prompt manageable
        max_ctx = 12000
        ctx = (context or "")[:max_ctx] if context else None
        full_prompt = prompt if not ctx else f"Context:\n{ctx}\n\nQuestion: {prompt}"
        try:
            response = self.model.generate_content(full_prompt)
            return (response.text or "").strip()
        except Exception as e:
            # Surface a concise error message while avoiding crash
            return f"LLM error: {str(e)}"

    def answer_about_image(self, image_path, question: str, ocr_hint: str | None = None):
        """Answer a question about an image using Gemini multimodal.

        Falls back to text-only using OCR hint if the model/image input fails.
        """
        try:
            from PIL import Image as _PILImage
            img = _PILImage.open(image_path)
            parts = [img, question]
            # Provide OCR/context as an additional hint if available
            if ocr_hint:
                parts = [img, f"OCR/context:\n{ocr_hint}\n\nQuestion: {question}"]
            resp = self.model.generate_content(parts)
            return (getattr(resp, 'text', '') or '').strip()
        except Exception:
            # Fallback to text-only using OCR hint if provided
            if ocr_hint:
                return self.answer(question, context=ocr_hint)
            return "LLM error: image question answering is unavailable. Try providing an OCR hint."