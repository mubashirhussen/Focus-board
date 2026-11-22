# FocusBoard — SaaS Billing, Plans & Entitlement Architecture

## 1. Overview
FocusBoard's SaaS billing architecture introduces tenant-aware subscriptions, configurable plan catalogs, atomic usage metering, and provider abstraction (supporting both Stripe and testable Mock providers).

---

## 2. Plan Hierarchy & Entitlements

| Plan Slug | Monthly Price | Active Tasks | Workspaces | Projects | Team Members | Monthly AI Requests | Daily Plans | Calendar Sync | Automations |
|---|---|---|---|---|---|---|---|---|---|
| **Free** | $0 | 50 | 1 | 1 | 2 | 15 | 5 | Disabled | Disabled |
| **Starter** | $9 | 200 | 3 | 5 | 5 | 100 | 30 | Enabled | Enabled |
| **Pro** | $19 | 1,000 | 10 | 25 | 15 | 500 | 100 | Enabled | Enabled |
| **Team** | $49 | 5,000 | 25 | 100 | 50 | 2,000 | 500 | Enabled | Enabled |
| **Enterprise** | $199 | Unlimited (-1) | Unlimited (-1) | Unlimited (-1) | Unlimited (-1) | 10,000 | Unlimited (-1) | Enabled | Enabled |

---

## 3. Quota Enforcement & Metering
- **Pre-execution Gate**: `check_entitlement(db, tenant_id, metric_name, increment)` is executed before expensive AI or task generation operations. If quota is exhausted, returns HTTP `402 Payment Required`.
- **Atomic Usage Persistence**: Resource consumption is committed to `usage_records` with active billing cycle boundaries (`period_start`, `period_end`).
- **Default Free Tier**: New tenants without an active subscription automatically initialize with the Free tier.

---

## 4. Billing Provider Abstraction
- Defined by `BillingProvider` base class with implementations:
  - `MockBillingProvider`: Enables instant, zero-external-dependency local testing and CI verification.
  - `StripeBillingProvider`: Connects to Stripe Checkout Sessions, Customer Portal, and Webhook dispatchers when `STRIPE_SECRET_KEY` is configured.
- **Idempotent Webhooks**: Authoritative subscription state updates (`checkout.session.completed`, `customer.subscription.deleted`) verify webhook events and persist status without trusting client-side claims.
