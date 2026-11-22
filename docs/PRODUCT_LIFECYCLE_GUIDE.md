# FocusBoard Product Lifecycle Intelligence & Growth Platform Guide (Phase 45)

## 1. Overview
Phase 45 transforms FocusBoard into an end-to-end Product Lifecycle Intelligence platform, bridging customer discovery, feature demand, RICE prioritization, strategic roadmaps, A/B experimentation, and release management.

---

## 2. Core Modules & Lifecycle Funnel

```
Customer Discovery ➔ Feature Requests ➔ Opportunity Analysis ➔ Prioritization (RICE/ICE) ➔ Initiatives ➔ Roadmap Scheduling ➔ A/B Testing ➔ Release & Retrospective
```

1. **Product Discovery & Ideas**:
   - Capture customer problems, formulate hypotheses, identify target user personas, and evaluate validation outcomes.
2. **Customer Demand Hub (Feature Requests)**:
   - Aggregate customer endorsements, track pipeline revenue impact from prospective deals, and merge duplicate requests cleanly.
3. **Prioritization Engine**:
   - **RICE Score**: `(Reach × Impact × Confidence) / Effort`
   - **ICE Score**: `Impact × Confidence × Ease`
   - **MoSCoW Categorization**: Must Have, Should Have, Could Have, Won't Have.
4. **Initiatives & Lifecycle Roadmaps**:
   - Link strategic company objectives to quarterly roadmap deliverables with progress tracking and dependency blockers.
5. **A/B Testing & Experimentation Platform**:
   - Deterministic user variant allocation (`control` vs. `treatment`), impression/conversion tracking, and live conversion rate calculation.
6. **Product Feature Releases & Retrospectives**:
   - Track rollout progress, document release notes, and record lessons learned and action items.
7. **Grounded AI Product Assistant**:
   - Grounded intelligence analyzing customer request volume, roadmap bottlenecks, and experiment results based strictly on live database records.

---

## 3. Data Models

| Model | Table Name | Purpose |
|---|---|---|
| `ProductDiscovery` | `product_discoveries` | Problem statement, hypothesis, and target segments. |
| `ProductIdea` | `product_ideas` | Solution concepts linked to discoveries. |
| `ProductFeatureRequest` | `product_feature_requests` | Customer demand requests with request counts and revenue impact. |
| `ProductOpportunity` | `product_opportunities` | Market opportunities with revenue potential and effort estimates. |
| `ProductPrioritizationItem` | `product_prioritization_items` | Scored items with RICE, ICE, and MoSCoW rankings. |
| `ProductInitiative` | `product_initiatives` | High-level strategic themes with progress percentages. |
| `LifecycleRoadmapItem` | `lifecycle_roadmap_items` | Quarterly timeline deliverables. |
| `RoadmapDependency` | `roadmap_dependencies` | Dependency relationships (`BLOCKS`, `REQUIRES`, `RELATES_TO`). |
| `ProductExperiment` | `product_experiments` | Growth experiments and hypotheses. |
| `ExperimentVariant` | `experiment_variants` | Allocation percentages and conversion tracking per variant. |
| `ProductRelease` | `product_releases` | Version rollouts and release notes. |
| `ProductRetrospective` | `product_retrospectives` | Post-release lessons learned and action items. |

---

## 4. API Endpoints

- `GET /api/v1/product-lifecycle/overview` — Funnel aggregates, demand counts, and revenue impact.
- `GET /api/v1/product-lifecycle/discoveries` — List problem discoveries.
- `POST /api/v1/product-lifecycle/discoveries` — Create problem discovery.
- `GET /api/v1/product-lifecycle/feature-requests` — Customer feature requests.
- `POST /api/v1/product-lifecycle/feature-requests/{id}/merge` — Merge duplicate requests.
- `POST /api/v1/product-lifecycle/prioritization/calculate` — Compute RICE/ICE scores.
- `GET /api/v1/product-lifecycle/roadmap` — Scheduled roadmap deliverables.
- `GET /api/v1/product-lifecycle/experiments` — Active A/B experiments and variants.
- `POST /api/v1/product-lifecycle/experiments/{id}/assign` — Deterministically assign user variant.
- `POST /api/v1/product-lifecycle/experiments/{id}/events` — Record conversion telemetry.
- `POST /api/v1/product-lifecycle/ai/query` — Grounded AI Product Assistant query.
