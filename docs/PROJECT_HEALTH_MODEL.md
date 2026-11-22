# FocusBoard Project Health & Risk Scoring Model

## 1. Principles
The FocusBoard Project Health Scoring algorithm is deterministic, transparent, and explainable. It avoids black-box heuristics and provides clear remediation signals for project managers.

---

## 2. Health Calculation Formula

```
Health Score = Max(0, Min(100, Base (100) - Deductions))
```

### Deduction Weights:
1. **Overdue Task Ratio (Max: 40 points)**
   ```
   Deduction = Min(40.0, (Overdue Open Tasks / Total Open Tasks) * 40.0)
   ```
2. **Active Risk Severity (Max: 35 points)**
   - Critical Risk: `-20 points` each
   - High Risk: `-10 points` each
   - Medium Risk: `-5 points` each
   - Capped at `-35 points` aggregate.
3. **Deadline Slippage (Max: 25 points)**
   - If `Project Deadline < Current Timestamp` and `Open Tasks > 0`: `-25 points`.

---

## 3. Status Classification

| Score Range | Status | Meaning |
| :--- | :--- | :--- |
| **80 – 100** | `HEALTHY` | On schedule, minimal risk exposure, velocity stable. |
| **50 – 79** | `AT_RISK` | Approaching deadline, minor bottlenecks, high risk detected. |
| **0 – 49** | `CRITICAL` | Major overdue blockers, critical risks unmitigated. |
| **N/A** | `INSUFFICIENT_DATA`| Project contains zero tasks. |

---

## 4. Delivery Forecasting Engine
- Calculates throughput over the previous 14 days (`Velocity = Tasks Completed / 14`).
- If throughput $\ge 2$ tasks:
  $$\text{Days Needed} = \frac{\text{Remaining Open Tasks}}{\text{Tasks Per Day}}$$
- Yields a statistical delivery window:
  ```json
  {
    "status": "forecasted",
    "completion_range": "Nov 28 - Dec 05, 2026",
    "message": "At current velocity (4.5 tasks/wk), completion estimated within 12 days."
  }
  ```
- If historical completions $< 2$, returns an honest explanation requesting additional completion history before forecasting.
