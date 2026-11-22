"""Example: Verifying incoming webhook deliveries from FocusBoard."""
from focusboard_sdk.client import FocusBoardClient

def handle_incoming_webhook(request_body: str, signature_header: str, webhook_secret: str):
    is_valid = FocusBoardClient.verify_webhook_signature(
        payload_str=request_body,
        signature_header=signature_header,
        secret_key=webhook_secret
    )

    if not is_valid:
        print("REJECTED: Webhook signature verification failed! Possible tampering or wrong secret.")
        return False

    print("VERIFIED: Webhook signature is authentic. Processing event safely.")
    return True

if __name__ == "__main__":
    # Example simulated payload and signature
    import time
    import hmac
    import hashlib

    secret = "whsec_test_secret_key_abcdef123456"
    sample_payload = '{"event": "task.created", "task_id": "task-12345", "title": "Deploy hotfix"}'
    ts = int(time.time())
    sig = hmac.new(secret.encode(), f"{ts}.{sample_payload}".encode(), hashlib.sha256).hexdigest()
    header = f"t={ts},v1={sig}"

    handle_incoming_webhook(sample_payload, header, secret)
