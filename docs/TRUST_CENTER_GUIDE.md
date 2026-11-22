# FocusBoard Public Trust Center & Security Architecture

## Overview
The FocusBoard Trust Center (`/trust` and `/api/v1/security/trust/overview`) serves as a public-facing portal providing prospective and existing enterprise customers with transparent visibility into our security posture, encryption specifications, subprocessor inventory, and compliance readiness statements.

---

## 1. Cryptographic Safeguards & System Architecture

### 1.1 In-Transit Protection
- **Protocol**: Transport Layer Security (TLS) 1.3 enforced across all ingress points.
- **Cipher Suites**: Modern forward-secrecy suites including `ECDHE-RSA-AES128-GCM-SHA256`.
- **Headers**: Strict-Transport-Security (HSTS) with `max-age=31536000; includeSubDomains`.
- **CORS**: Domain whitelisting with credentials isolation.

### 1.2 At-Rest Protection
- **Database Tablespaces**: PostgreSQL encrypted with AES-256 GCM.
- **Artifacts & Attachments**: AWS S3 server-side encryption with KMS customer-managed keys.
- **Sensitive Credentials**: API keys, webhooks secrets, and tokens hashed using bcrypt or encrypted with AES-256 before disk writes.

### 1.3 Tenant Isolation
- **Row-Level & Schema Isolation**: Every query validates `user_id`, `workspace_id`, and `organization_id` boundaries.
- **Zero Cross-Tenant Leakage**: Automated integration tests strictly verify that cross-tenant access attempts return HTTP 403/404.

---

## 2. Approved Third-Party Subprocessor Directory

To guarantee compliance with GDPR Article 28 and enterprise Data Processing Agreements (DPAs), FocusBoard maintains an active subprocessor directory:

| Subprocessor | Purpose | Jurisdiction | Verified Standards |
|:---|:---|:---|:---|
| **Amazon Web Services (AWS)** | Cloud Hosting & Aurora PostgreSQL Multi-AZ | United States / EU | SOC 2 Type II, ISO 27001, PCI-DSS Level 1 |
| **Cloudflare** | Edge CDN, DDoS Shield & WAF | Global Edge | SOC 2 Type II, ISO 27001, PCI-DSS |
| **Stripe** | Payment Engine & Billing Tokenization | United States | PCI-DSS Level 1, SOC 1, SOC 2 |
| **OpenAI / Anthropic** | AI Copilot Inference (Zero Data Retention) | United States | SOC 2 Type II, GDPR DPA |

---

## 3. Public Documents & Whitepapers

The Trust Center publishes reviewed security documents:
1. `DOC-SOC2-READINESS`: SOC 2 Type II Readiness Report & Control Matrix.
2. `DOC-ISO27001-SOA`: ISO/IEC 27001 Statement of Applicability.
3. `DOC-SUBPROCESSOR-LIST`: Approved Third-Party Subprocessor Directory.
4. `DOC-SEC-WHITEPAPER`: FocusBoard Enterprise Security & Architecture Whitepaper.
