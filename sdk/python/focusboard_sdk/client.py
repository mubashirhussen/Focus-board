import json
import hmac
import hashlib
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

class FocusBoardClient:
    """Official Python SDK Client for FocusBoard Public API."""

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000/api/v1/public/v1"):
        if not api_key:
            raise ValueError("api_key must be provided")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        req_headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if headers:
            req_headers.update(headers)

        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status == 204:
                    return None
                resp_data = resp.read().decode("utf-8")
                return json.loads(resp_data) if resp_data else None
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_body)
                raise RuntimeError(f"FocusBoard API Error ({e.code}): {err_json.get('detail', err_body)}")
            except Exception:
                raise RuntimeError(f"FocusBoard API Error ({e.code}): {err_body}")

    # Task Operations
    def list_tasks(self, status: Optional[str] = None, project_id: Optional[int] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        query_parts = [f"limit={limit}", f"offset={offset}"]
        if status:
            query_parts.append(f"status={status}")
        if project_id:
            query_parts.append(f"project_id={project_id}")
        query_str = "&".join(query_parts)
        return self._request("GET", f"tasks?{query_str}")

    def create_task(self, title: str, description: Optional[str] = None, due_date: Optional[str] = None, priority: str = "medium", category: str = "General", project_id: Optional[int] = None, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "category": category,
            "project_id": project_id,
        }
        headers = {}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return self._request("POST", "tasks", payload=payload, headers=headers)

    def get_task(self, task_id: str) -> Dict[str, Any]:
        return self._request("GET", f"tasks/{task_id}")

    def update_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        return self._request("PATCH", f"tasks/{task_id}", payload=kwargs)

    def delete_task(self, task_id: str) -> None:
        self._request("DELETE", f"tasks/{task_id}")

    # Projects
    def list_projects(self) -> List[Dict[str, Any]]:
        return self._request("GET", "projects")

    # Analytics
    def get_portfolio_analytics(self) -> Dict[str, Any]:
        return self._request("GET", "analytics/portfolio")

    # Webhook Verification
    @staticmethod
    def verify_webhook_signature(payload_str: str, signature_header: str, secret_key: str, tolerance_seconds: int = 300) -> bool:
        """Verifies X-FocusBoard-Signature (format: 't=1234567890,v1=abcde...')."""
        try:
            parts = dict(item.split("=", 1) for item in signature_header.split(","))
            ts = parts.get("t")
            sig = parts.get("v1")
            if not ts or not sig:
                return False

            to_sign = f"{ts}.{payload_str}".encode("utf-8")
            expected_sig = hmac.new(secret_key.encode("utf-8"), to_sign, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected_sig, sig)
        except Exception:
            return False
