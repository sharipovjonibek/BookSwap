
import os, json, re
from typing import Dict, Any
from django.conf import settings

try:
    from google import genai
    _GENAI = True
except Exception:
    genai = None
    _GENAI = False

SYSTEM_INSTRUCTIONS = (
    "You are a helpful AI librarian. The user describes their problem/goal. "
    "Return ONLY a compact JSON with this exact schema:\n"
    "{\n"
    "  \"query_intent\": \"string\",\n"
    "  \"topics\": [\"string\"],\n"
    "  \"suggested_books\": [\n"
    "     { \"title\": \"string\", \"author\": \"string\", \"why\": \"one-sentence reason\" }\n"
    "  ]\n"
    "}"
)

def _strip_fences(t: str) -> str:
    t = t.strip()
    t = re.sub(r'^```(?:json)?\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*```$', '', t)
    return t

def get_ai_advice(prompt: str) -> Dict[str, Any]:
    api_key = "AIzaSyB4nep6VvcD5B6YylM8NJ849oZFyyLklFo"
    model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")

    if not _GENAI or not api_key:
        return {
            "query_intent": prompt.strip()[:160],
            "topics": [w for w in re.findall(r"[a-zA-Z]{4,}", prompt.lower())][:5],
            "suggested_books": [
                {"title":"Atomic Habits","author":"James Clear","why":"Build good habits and break bad ones."},
                {"title":"Deep Work","author":"Cal Newport","why":"Learn deep focus and reduce distraction."},
                {"title":"Mindset","author":"Carol Dweck","why":"Adopt a growth mindset for change."},
            ],
            "_warning":"Gemini not configured — using fallback suggestions."
        }

    try:
        client = genai.Client(api_key=api_key)
        user_text = f"User prompt: {prompt}\n\n{SYSTEM_INSTRUCTIONS}"
        resp = client.models.generate_content(
            model=model,
            contents=user_text,
            config={"response_mime_type":"application/json"}
        )
        raw = getattr(resp, "text", None) or getattr(resp, "output_text", None) or ""
        raw = _strip_fences(str(raw))
        return json.loads(raw)
    except Exception as e:
        # Never crash API: return safe empty payload
        return {"query_intent": prompt.strip()[:160], "topics": [], "suggested_books": [], "_warning": f"AI error: {e.__class__.__name__}"}
