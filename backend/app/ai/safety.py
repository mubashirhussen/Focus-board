import re

# High-risk prompt injection keywords and malicious pattern signatures
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s*prompt",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"bypass\s+(all\s+)?security",
    r"drop\s+table",
    r"delete\s+from\s+users",
    r"<script>",
    r"exec\s*\(",
    r"eval\s*\(",
]

def sanitize_user_input(text: str, max_chars: int = 2000) -> str:
    """Sanitize and truncate untrusted user input before passing to AI service."""
    if not text:
        return ""
    truncated = text[:max_chars].strip()
    return truncated

def check_prompt_safety(text: str) -> bool:
    """Check if the text contains obvious adversarial prompt injection attempts."""
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    return True
