# FocusBoard Domain Configuration & TLS/HTTPS Guide

## 1. Domain Architecture
In production, FocusBoard separates frontend static assets from backend API services using subdomains:
- **Application Frontend**: `app.focusboard.app` (or root `focusboard.app`)
- **Backend API**: `api.focusboard.app`
- **Staging Frontend**: `staging.focusboard.app`
- **Staging API**: `api-staging.focusboard.app`

---

## 2. DNS Record Configuration Template

Add the following DNS records in your domain registrar (e.g. Cloudflare, Namecheap, Route 53):

| Type | Name | Content / Target | Proxy Status | TTL |
|---|---|---|---|---|
| **CNAME** | `app` | `cname.vercel-dns.com` (or Cloudflare Pages target) | Proxied (Orange Cloud) | Auto |
| **CNAME** | `api` | `focusboard-backend.onrender.com` (or Railway target) | DNS Only / Proxied | Auto |
| **TXT** | `@` | `focusboard-domain-verification=fb-token-...` | DNS Only | Auto |
| **CAA** | `@` | `0 issue "letsencrypt.org"` | DNS Only | Auto |

---

## 3. HTTPS / TLS Encryption Standards
- **TLS Version**: TLS 1.3 enforced (TLS 1.2 minimum).
- **Certificate Authority**: Automated Let's Encrypt / Cloudflare Edge SSL.
- **HSTS (HTTP Strict Transport Security)**:
  `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- **HTTP to HTTPS Redirection**: Automatically enforced by both Nginx and Vercel edge routers.
- **Secure Cookie Settings**:
  - `Secure`: Always true in production.
  - `HttpOnly`: Enforced on session tokens.
  - `SameSite`: `Lax` or `Strict`.

---

## 4. Verification & Troubleshooting
To verify SSL certificate validity and HTTP-to-HTTPS redirection:
```bash
curl -I https://api.focusboard.app/health
curl -I http://api.focusboard.app/health  # Should return HTTP 301/308 redirect to https
```
