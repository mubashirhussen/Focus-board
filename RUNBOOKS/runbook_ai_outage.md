# Runbook: AI Provider Outage & Rate Limiting

## 1. Trigger & Severity
- **Trigger**: AI assistant, daily planner, or coach endpoints return HTTP 504 / 429; external provider (Gemini / Anthropic / OpenAI) latency > 10 seconds.
- **Severity**: **SEV-3** (Core task management, boards, and collaboration remain 100% operational).

## 2. Immediate Diagnostic Steps
1. Verify AI provider status page (e.g. Google Cloud / Gemini API status).
2. Check backend logs for rate limit (`429 Too Many Requests`) or timeout errors.
3. Verify that the deterministic knapsack daily planner fallback activates automatically.

## 3. Resolution Procedures
- **Deterministic Offline Fallback**:
  FocusBoard automatically falls back to local mathematical knapsack prioritization and rule-based scheduling when the external AI provider is unreachable.
- **Rotate API Keys**:
  If quota exhaustion occurred, update `GEMINI_API_KEY` in cloud environment variables.
- **Switch Provider**:
  Change `AI_PROVIDER=anthropic` or `AI_PROVIDER=openai` in cloud configuration.

## 4. Post-Recovery Verification
Test AI endpoint directly:
```bash
curl -X POST https://api.focusboard.app/api/v1/ai/priorities -H "Authorization: Bearer <token>"
```
