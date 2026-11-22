# FocusBoard SaaS Financial Intelligence, Revenue Analytics & FinOps Guide

## Overview
Phase 35 equips FocusBoard with deep SaaS financial intelligence, normalized recurring revenue analytics, customer unit economics, and cloud/AI FinOps cost attribution. The system provides executive decision-makers with real-time insight into top-line sustainability, gross margin health, and forward scenario projections.

---

## 1. Revenue Metrics & Normalization

### 1.1 Normalized MRR & ARR
Recurring subscriptions are normalized to 30-day monthly intervals:
- **Monthly Subscription**: Price added directly to MRR.
- **Annual Subscription**: Price divided by 12 before MRR summation.
- **Annual Run Rate (ARR)**: Calculated precisely as $\text{ARR} = \text{MRR} \times 12$.
- **Exclusions**: Unpaid invoices, trialing accounts, and one-time setup fees are excluded from recurring revenue baselines.

### 1.2 MRR Movements Waterfall
Tracked on a monthly cohort basis:
$$\text{Net New MRR} = \text{New MRR} + \text{Expansion MRR} - \text{Contraction MRR} - \text{Churned MRR}$$

---

## 2. Customer Retention & Churn Analytics

### 2.1 Logo & Customer Churn Rate
$$\text{Customer Churn Rate} = \left( \frac{\text{Canceled Subscriptions in Period}}{\text{Active Subscriptions at Start}} \right) \times 100$$

### 2.2 Gross Revenue Retention (GRR)
Measures retained revenue excluding expansions (capped at 100%):
$$\text{GRR} = \max\left(0, 100 - \text{MRR Churn Rate} - \text{Contraction Rate}\right)$$

### 2.3 Net Revenue Retention (NRR)
Measures net revenue growth from existing customer cohorts including seat upgrades and tier expansions:
$$\text{NRR} = \text{GRR} + \text{Expansion Rate}$$
- Healthy enterprise B2B SaaS benchmark: $105\% - 125\%$.

---

## 3. SaaS Unit Economics

1. **Average Revenue Per User (ARPU)**:
   $$\text{ARPU} = \frac{\text{Total MRR}}{\text{Paying Tenants Count}}$$

2. **Customer Lifetime Value (LTV)**:
   $$\text{LTV} = \frac{\text{ARPU}}{\text{Customer Churn Rate}}$$

3. **LTV / CAC Ratio**:
   $$\text{LTV/CAC} = \frac{\text{LTV}}{\text{Customer Acquisition Cost}}$$
   - Target: $\ge 3.0\times$ (capital-efficient SaaS).

4. **CAC Payback Period**:
   $$\text{Payback Months} = \frac{\text{CAC}}{\text{ARPU} \times \text{Gross Margin \%}}$$

---

## 4. FinOps & Cloud/AI Cost Attribution

Direct Cost of Goods Sold (COGS) is tracked across infrastructure providers:
- **Cloud Infrastructure**: Kubernetes EKS nodes, load balancers, and FastAPI worker clusters.
- **AI Inference**: Token consumption from `ai_agent_executions` attributed to tasks and copilots.
- **Database & Storage**: PostgreSQL Aurora multi-AZ instances and AWS S3 artifact storage.

### Gross Margin Formula
$$\text{Gross Margin \%} = \left( \frac{\text{Net Revenue} - \text{Direct COGS}}{\text{Net Revenue}} \right) \times 100$$
- FocusBoard targets a gross margin $> 75\%$, reflecting an efficient serverless and cached architecture.

---

## 5. Budget Controls & Multi-Scenario Projections

### 5.1 Budget Threshold Alerts
Budgets define monthly or quarterly limits with configurable warning thresholds (e.g., 80%). When actual expenses exceed this ratio, the system triggers real-time operational alerts in the dashboard.

### 5.2 Scenario Modeling
Projections model 3-month forward horizons across three business conditions:
1. **BASELINE**: 6% MoM compound growth.
2. **GROWTH**: 15% MoM compound growth.
3. **CONSERVATIVE**: 1% MoM compound growth.

---

## 6. Financial Data Export API
Executive summaries, full transaction ledgers, and raw FinOps cost logs can be exported directly via:
- Endpoint: `POST /api/v1/finance/reports/export`
- Payload: `{"report_type": "EXECUTIVE_SUMMARY", "format": "CSV"}`
