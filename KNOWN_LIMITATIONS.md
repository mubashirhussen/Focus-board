# FocusBoard: Known Limitations & Future Roadmap

## 1. Current Architectural Limitations

### 1.1 Multi-Region Database Writes
- The current database architecture is optimized for single-primary managed PostgreSQL with read replicas.
- Multi-region active-active writes are not currently supported; all write transactions route through the primary database region.

### 1.2 Offline Attachment Uploads
- Task metadata, titles, priorities, and status transitions sync seamlessly offline via IndexedDB.
- Large binary file attachments are queued until an active, high-bandwidth connection is detected.

### 1.3 External AI Provider Quotas
- When using external AI models (Gemini / Anthropic / OpenAI), requests are subject to third-party provider API rate limits. FocusBoard provides a deterministic mathematical knapsack fallback that operates offline.

---

## 2. Future Architectural Enhancements
1. **Automated Read Replica Routing**: Route read-heavy analytics and search queries to read replicas.
2. **WebAuthn / Passkeys**: Add FIDO2 biometric passkey authentication alongside TOTP MFA.
3. **Advanced Workflow Canvas**: Visual drag-and-drop workflow automation editor.
