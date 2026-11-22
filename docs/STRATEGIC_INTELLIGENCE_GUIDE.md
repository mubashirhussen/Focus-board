# FocusBoard SaaS Platform Strategic Intelligence Guide (Phase 36)

## 1. Overview
Phase 36 introduces the Strategic Intelligence & Market Decision Engine into FocusBoard. It bridges operational task execution and executive strategy by connecting business analytics, market signals, competitor benchmarking, RICE prioritization, and grounded AI strategic guidance.

---

## 2. Architecture & Data Model

### Key Models (`backend/app/models/strategic_intelligence.py`)
- **`StrategicPlan`**: Top-level strategic horizons (Annual, 3-Year, Quarterly) with vision, mission, and strategic themes.
- **`StrategicGoal`**: Quantifiable targets with `baseline_value`, `target_value`, `current_value`, `unit`, and dynamic `progress_percentage`.
- **`StrategicInitiative`**: Cross-functional execution streams supporting goals with priorities (`P1_CRITICAL` through `P4_LOW`) and assigned budgets.
- **`MarketIntelligence` & `MarketSignal`**: Qualitative and quantitative telemetry covering growth, pricing shifts, customer demand, and competitor moves.
- **`Competitor`**: Detailed competitive profiles tracking market position, pricing models, feature differentiation matrices, and threat levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **`SWOTEntry`**: Internal strengths/weaknesses and external opportunities/threats with verifiable evidence references.
- **`MarketSizing`**: Transparent TAM (Total Addressable Market), SAM (Serviceable Addressable Market), and SOM (Serviceable Obtainable Market) calculations with transparent bottom-up/top-down assumptions.
- **`StrategicOpportunity`**: Opportunity pipeline evaluated using the standardized RICE scoring model:
  $$\text{RICE Score} = \frac{\text{Reach} \times \text{Impact} \times \text{Confidence}}{\text{Effort}}$$
- **`StrategicScenario` & `StrategicDecision`**: Scenario models (Best, Base, Worst case) and auditable strategic decision logs.

---

## 3. REST API Endpoints (`/api/v1/strategy`)
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/strategy/overview` | `GET` | Executive dashboard overview including goal progress, competitor threats, and AI recommendations |
| `/strategy/plans` | `GET`, `POST` | List and create multi-year strategic plans |
| `/strategy/goals` | `GET`, `POST` | Track strategic goals with automated progress recalculation |
| `/strategy/initiatives` | `GET`, `POST` | Manage execution initiatives and budgets |
| `/strategy/opportunities` | `GET`, `POST` | Register opportunities with automated RICE scoring |
| `/strategy/competitors` | `GET`, `POST` | Manage competitor benchmarking profiles and threat ratings |
| `/strategy/swot` | `GET`, `POST` | Manage SWOT matrix entries and evidence backing |
| `/strategy/market-sizing` | `GET`, `POST` | Transparent TAM/SAM/SOM sizing and assumption models |
| `/strategy/decisions` | `GET`, `POST` | Maintain auditable executive decision log |

---

## 4. Grounded AI Strategy Analyst
The AI Strategy Analyst generates actionable recommendations grounded in real database telemetry—never fabricating numbers or unsubstantiated claims. Every recommendation links directly to verified telemetry records (`grounded_evidence`).
