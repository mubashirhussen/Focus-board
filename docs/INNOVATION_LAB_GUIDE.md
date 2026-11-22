# FocusBoard Innovation Lab, R&D & Prototyping Pipeline Guide (Phase 37)

## 1. Overview
The FocusBoard Innovation Lab provides a structured, scientific R&D lifecycle for capturing ideas, articulating measurable hypotheses, executing controlled experiments, developing technical prototypes, validating problem-solution fit, and promoting proven innovations directly to the production product roadmap.

---

## 2. Stage Progression Lifecycle
Ideas progress sequentially through standard pipeline stages:
1. **`CAPTURE`**: Initial ideation and problem-solution articulation.
2. **`SCREENING`**: Strategic alignment evaluation against innovation portfolios.
3. **`RESEARCH`**: Deep-dive market and user research.
4. **`HYPOTHESIS`**: Formal falsifiable hypothesis definition: *"We believe [target audience] will [behavior] because [reason]..."* with explicit quantitative criteria.
5. **`EXPERIMENTATION`**: Running customer interviews, surveys, prototype tests, A/B experiments, or technical PoCs.
6. **`PROTOTYPE`**: Interactive mockups and engineering PoCs with tracked demo and repository URLs.
7. **`VALIDATED`**: Multi-dimensional verification (Problem, Customer, Market, Technical, Business, Security).
8. **`ROADMAP`**: One-click promotion to `ProductRoadmapItem` with automated status updating.

---

## 3. REST API Endpoints (`/api/v1/innovation`)
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/innovation/overview` | `GET` | Pipeline counts, active experiments, success rates, and prototypes |
| `/innovation/ideas` | `GET`, `POST` | List and submit innovation ideas |
| `/innovation/ideas/{id}` | `GET`, `PATCH`, `DELETE` | Retrieve and update idea lifecycle stage |
| `/innovation/ideas/{id}/promote-to-roadmap` | `POST` | Converts validated idea into production `ProductRoadmapItem` |
| `/innovation/hypotheses` | `GET`, `POST`, `PATCH` | Manage measurable falsifiable hypotheses |
| `/innovation/experiments` | `GET`, `POST`, `PATCH` | Manage experiments and budget allocations |
| `/innovation/experiments/{id}/results` | `GET`, `POST` | Record quantitative summaries and lessons learned |
| `/innovation/prototypes` | `GET`, `POST`, `PATCH` | Track demo links, tech stacks, and PoC status |
| `/innovation/validations` | `GET`, `POST` | Multi-dimensional validation records across 6 key pillars |
| `/innovation/portfolios` | `GET`, `POST` | Manage R&D focus areas and spend limits |
