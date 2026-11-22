import re
import json
from typing import Dict, Any, Optional

# High-risk prompt injection keywords and malicious pattern signatures
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|system)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
    r"reveal\s+(the\s+)?(system|internal)\s*prompt",
    r"print\s+(the\s+)?(system|internal)\s*prompt",
    r"you\s+are\s+now\s+(in\s+)?(developer\s+mode|dan|jailbroken)",
    r"bypass\s+(all\s+)?(security|authorization|rules)",
    r"drop\s+table",
    r"delete\s+from\s+users",
    r"<script>",
    r"exec\s*\(",
    r"eval\s*\(",
    r"secret[_\s-]?key",
    r"api[_\s-]?key",
]

def sanitize_user_input(text: str, max_chars: int = 2000) -> str:
    """Sanitize and truncate untrusted user input before passing to AI service."""
    if not text:
        return ""
    # Strip potential prompt escaping tags
    cleaned = text.replace("<focusboard_authorized_context>", "").replace("</focusboard_authorized_context>", "")
    # Strip control chars
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)
    return cleaned[:max_chars].strip()

def check_prompt_safety(text: str) -> bool:
    """Check if the text contains obvious adversarial prompt injection attempts."""
    if not text:
        return True
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    return True

def sanitize_ai_output(text: str) -> str:
    """Sanitize AI output to eliminate XSS or executable spreadsheet payloads."""
    if not text:
        return ""
    # Strip script tags
    sanitized = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
    return sanitized

def parse_and_validate_json(raw_text: str, default_fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract and parse JSON object from LLM response safely."""
    if not raw_text:
        return default_fallback or {}

    try:
        # Match outermost JSON object or array
        match = re.search(r"(\{.*\}|\[.*\])", raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return json.loads(raw_text)
    except Exception:
        return default_fallback or {}
