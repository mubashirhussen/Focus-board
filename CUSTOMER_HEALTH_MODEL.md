# FocusBoard Customer Health Score Telemetry Model
## Explainable, Real-Time Account Health Calculation

FocusBoard implements a deterministic, explainable Customer Health Score model (`GET /api/v1/support/customer-health`) derived purely from actual database telemetry, completely eliminating fabricated or arbitrary numbers.

---

## 1. Health Score Formula & Weight Distribution

The Customer Health Score is calculated on a 0 - 100 scale:

$$\text{Health Score} = \text{Base (100)} - \text{Completion Velocity Penalty} - \text{Overdue Penalty} - \text{Open Ticket Penalty}$$

### Component Breakdown
1. **Task Completion Ratio (Weight: 50 points)**:
   - Evaluates the user's workload velocity: $\frac{\text{Completed Tasks}}{\text{Total Tasks}} \times 100$.
   - If velocity $\ge 70\%$: 0 penalty.
   - If velocity is between $40\%$ and $69\%$: 15 point penalty.
   - If velocity $< 40\%$: 30 point penalty.
   - *If no tasks exist yet (new account)*: 0 penalty (grace period).

2. **Overdue Task Ratio (Weight: 30 points)**:
   - Counts active tasks whose `due_date < NOW()`.
   - 0 overdue tasks: 0 penalty.
   - 1 - 2 overdue tasks: 10 point penalty.
   - 3+ overdue tasks: 25 point penalty.

3. **Active Critical Tickets (Weight: 20 points)**:
   - Evaluates open support tickets with priority `URGENT` or `HIGH`.
   - 0 open critical tickets: 0 penalty.
   - 1 open critical ticket: 10 point penalty.
   - 2+ open critical tickets: 20 point penalty.

---

## 2. Health Tier Categorization

| Score Range | Status | Meaning | Recommended Intervention |
| :--- | :--- | :--- | :--- |
| **85 – 100** | `HEALTHY` | Optimal engagement, high velocity, minimal friction. | Candidate for annual plan upgrade or referral. |
| **60 – 84** | `NEEDS_ATTENTION` | Moderate backlog accumulation or pending support inquiry. | In-app productivity tips or backlog review prompt. |
| **0 – 59** | `AT_RISK` | High overdue count, low completion rate, or unresolved critical tickets. | Proactive customer success check-in / SLA escalation. |

---

## 3. Explainability & Actionable Recommendations

The API returns not just the score, but structured actionable advice:
```json
{
  "health_score": 92,
  "health_status": "HEALTHY",
  "metrics": {
    "total_tasks": 24,
    "completed_tasks": 19,
    "completion_rate": 79.2,
    "overdue_tasks": 1,
    "open_urgent_tickets": 0
  },
  "recommendations": [
    "Reschedule 1 overdue task to maintain full velocity.",
    "Your workspace velocity is in the top 15% of active teams."
  ]
}
```
This ensures customer success teams and administrators understand exactly why a score changed and what concrete action resolves it.
