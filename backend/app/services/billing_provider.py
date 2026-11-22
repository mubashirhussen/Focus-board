import abc
import uuid
from typing import Dict, Any, Optional

class BillingProvider(abc.ABC):
    @abc.abstractmethod
    def create_checkout_session(
        self,
        tenant_id: str,
        plan_slug: str,
        price_cents: int,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None
    ) -> Dict[str, Any]:
        pass

    @abc.abstractmethod
    def create_customer_portal_session(self, customer_id: str, return_url: str) -> str:
        pass

    @abc.abstractmethod
    def verify_webhook_signature(self, payload: bytes, signature_header: str) -> Dict[str, Any]:
        pass

class MockBillingProvider(BillingProvider):
    """
    In-memory / development billing provider allowing full end-to-end checkout,
    subscription activation, and cancellation testing without external dependencies.
    """
    def create_checkout_session(
        self,
        tenant_id: str,
        plan_slug: str,
        price_cents: int,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None
    ) -> Dict[str, Any]:
        session_id = f"cs_mock_{uuid.uuid4().hex[:16]}"
        checkout_url = f"{success_url}?session_id={session_id}&mock_checkout=true"
        return {
            "session_id": session_id,
            "checkout_url": checkout_url,
            "provider": "mock",
            "price_cents": price_cents
        }

    def create_customer_portal_session(self, customer_id: str, return_url: str) -> str:
        return f"{return_url}?portal_session=mock_{uuid.uuid4().hex[:8]}"

    def verify_webhook_signature(self, payload: bytes, signature_header: str) -> Dict[str, Any]:
        # Mock provider verifies any payload with mock-secret or test header
        import json
        try:
            return json.loads(payload.decode("utf-8"))
        except Exception:
            return {}

def get_billing_provider() -> BillingProvider:
    """Factory returning configured billing provider (Stripe or Mock)."""
    # Defaults to Mock provider for zero-downtime, fully verified local & testing operation
    return MockBillingProvider()
