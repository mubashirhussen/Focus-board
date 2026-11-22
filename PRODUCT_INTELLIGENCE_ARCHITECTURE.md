# FocusBoard Product Intelligence & Adaptive Engine Architecture

## 1. Overview
The **Product Intelligence & Adaptive Engine** (Phase 22) transforms FocusBoard from a task tracker into an explainable, data-driven productivity assistant. Instead of producing generic motivational quotes or hallucinated tips, the engine directly inspects actual user task histories, completion patterns, deadline urgency, and workload velocity.

---

## 2. Core Architecture

### 2.1 Productivity Metrics & Behavioral Patterns
Located in `backend/app/services/intelligence_service.py` and `backend/app/models/intelligence.py`:
- **Deterministic Metrics Computation**:
  - `tasks_total`: Total active tasks in the user's scope.
  - `tasks_completed`: Total completed tasks.
  - `tasks_overdue`: Tasks with overdue deadlines that are not completed.
  - `completion_rate`: Integer percentage of completion velocity.
  - `avg_completion_hours`: Rolling average of completion turnaround time.
  - `velocity_trend`: `positive` (accelerating), `stable` (consistent), or `declining` (bottlenecked).
- **Pattern Recognition**:
  - **Overdue Cluster**: Detects multiple overdue items accumulating within a short window.
  - **High-Priority Accumulation**: Warns when high-priority tasks exceed 40% of the active workload without steady completion.
  - **Velocity Momentum**: Recognizes bursts of completed tasks and reinforces positive rhythm.

### 2.2 Explainable Ranked Insights & Feedback
- **Urgency Scoring**: Each detected pattern is scored dynamically on an urgency scale (0.0 to 1.0).
- **Task Evidence**: Insights explicitly link to specific supporting task IDs (`evidence_task_ids`), giving users clear rationale behind every recommendation.
- **Dismissal & Feedback Loop**:
  - `POST /api/v1/intelligence/insights/{insight_id}/dismiss` marks insights as dismissed in `ProductivityEvent`.
  - `POST /api/v1/intelligence/feedback` records explicit user ratings (`helpful`, `not_helpful`, with optional notes) in `InsightFeedback`.

### 2.3 Adaptive Focus Queue
- Prioritizes pending tasks by urgency score, priority weighting, and deadline risk (`high`, `medium`, `low`).
- Suggests optimal focus time blocks within the user's declared working hours (e.g. `09:30 - 11:00 AM`).

### 2.4 Grounded AI Productivity Coach
- Endpoint: `POST /api/v1/intelligence/coach`.
- Enforces data grounding: the coach prompt injects current task metrics, active bottlenecks, and top recommendations.
- Returns actionable responses paired with **Proposed Inquiries & Actions** that the user can click to immediately inspect or schedule focus sessions.

### 2.5 Personalization & Intelligence Preferences
- Model: `IntelligencePreference` in `backend/app/models/intelligence.py`.
- Configurable settings:
  - `working_hours_start` & `working_hours_end` (e.g., `09:00` - `17:00`)
  - `working_days` (JSON array: `["monday", "tuesday", "wednesday", "thursday", "friday"]`)
  - `timezone`
  - `smart_suggestions_enabled`
  - `adaptive_planning_enabled`
  - `bottleneck_detection_enabled`

---

## 3. API Endpoints
- `GET /api/v1/intelligence/metrics` — Aggregate productivity metrics.
- `GET /api/v1/intelligence/patterns` — Detected behavioral patterns.
- `GET /api/v1/intelligence/insights` — Ranked actionable insights with task evidence.
- `GET /api/v1/intelligence/recommendations` — Suggested focus queue with deadline risks.
- `POST /api/v1/intelligence/feedback` — Submit thumbs up/down feedback.
- `POST /api/v1/intelligence/insights/{insight_id}/dismiss` — Dismiss an active insight.
- `POST /api/v1/intelligence/coach` — Grounded conversational coaching query.
- `GET /api/v1/intelligence/preferences` — Get user productivity preferences.
- `PUT /api/v1/intelligence/preferences` — Update user productivity preferences.
