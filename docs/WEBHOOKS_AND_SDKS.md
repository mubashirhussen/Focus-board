# FocusBoard Webhooks & Official SDKs

## 1. Webhooks Architecture
FocusBoard delivers real-time notifications to your servers whenever events occur in your workspace.

### Available Events
- `task.created`
- `task.updated`
- `task.completed`
- `task.deleted`
- `webhook.test`

### HMAC-SHA256 Signature Verification
Each delivery includes the header:
```http
X-FocusBoard-Signature: t=1795333000,v1=5d41402abc4b2a76b9719d911017c592...
```
Where:
- `t` is the Unix timestamp of dispatch.
- `v1` is `HMAC-SHA256(secret_key, f"{t}.{payload_json}")`.

---

## 2. Python SDK Usage

### Installation
Include the `focusboard_sdk` package or copy `sdk/python/focusboard_sdk` into your project.

### Example Code
```python
from focusboard_sdk.client import FocusBoardClient

client = FocusBoardClient(api_key="fb_live_YOUR_KEY")

# Create task
task = client.create_task(
    title="Automated Security Scan",
    priority="high",
    category="Security",
    idempotency_key="sec-scan-run-1092"
)

print("Created Task:", task["id"])

# Verify Webhook
is_authentic = FocusBoardClient.verify_webhook_signature(
    payload_str=raw_body,
    signature_header=headers["X-FocusBoard-Signature"],
    secret_key="whsec_YOUR_SECRET"
)
```

---

## 3. TypeScript SDK Usage

```typescript
import { FocusBoardClient } from '@focusboard/sdk';

const client = new FocusBoardClient({
  apiKey: 'fb_live_YOUR_KEY',
});

// List open tasks
const tasks = await client.listTasks({ status: 'pending' });

// Verify Webhook Delivery
const isValid = FocusBoardClient.verifyWebhookSignature(
  rawBodyString,
  req.headers['x-focusboard-signature'],
  process.env.FOCUSBOARD_WEBHOOK_SECRET!
);
```
