import logging
import re
import sys
from typing import Any, Dict

SENSITIVE_KEY_PATTERNS = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"authorization", re.IGNORECASE),
    re.compile(r"cookie", re.IGNORECASE),
    re.compile(r"api[-_]?key", re.IGNORECASE),
    re.compile(r"credit[-_]?card", re.IGNORECASE),
    re.compile(r"card[-_]?num", re.IGNORECASE),
    re.compile(r"cvv", re.IGNORECASE),
]

def mask_sensitive_data(data: Any) -> Any:
    """Recursively masks sensitive keys and values in dictionaries and lists."""
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if any(p.search(str(key)) for p in SENSITIVE_KEY_PATTERNS):
                masked[key] = "[REDACTED]"
            elif isinstance(value, (dict, list)):
                masked[key] = mask_sensitive_data(value)
            else:
                masked[key] = value
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data

class SafeFormatter(logging.Formatter):
    """Custom formatter that automatically suppresses sensitive information in log output."""
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # Prevent leaking raw bearer tokens in standard log strings
        msg = re.sub(r"(Bearer\s+)[A-Za-z0-9_\-\.]+", r"\1[REDACTED_JWT]", msg)
        return msg

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configures centralized structured logging for FocusBoard."""
    logger = logging.getLogger("focusboard")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        formatter = SafeFormatter(
            fmt="%(asctime)s [%(levelname)s] [ReqID: %(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    logger.propagate = False
    return logger
