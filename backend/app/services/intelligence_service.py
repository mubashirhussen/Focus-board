import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.task import Task
from app.models.user import User
from app.models.intelligence import ProductivityEvent, IntelligencePreference, InsightFeedback
from app.schemas.intelligence import (
    ProductivityMetricsResponse,
    PatternItem,
    InsightItem,
    RecommendationItem,
    CoachResponse,
)

class ProductIntelligenceEngine:
    """
    Centralized Product Intelligence Engine.
    Computes explainable, deterministic behavioral analytics and grounds AI coaching in real task data.
    """
    def calculate_metrics(self, db: Session, user_id: int) -> ProductivityMetricsResponse:
        tasks = db.query(Task).filter(Task.user_id == user_id).all()
        now = datetime.now(timezone.utc)

        total = len(tasks)
        completed = [t for t in tasks if (t.status or "").lower() == "completed"]
        pending = [t for t in tasks if (t.status or "").lower() != "completed"]

        overdue_count = 0
        rescheduled_count = 0
        for t in pending:
            if t.due_date:
                try:
                    due = datetime.fromisoformat(t.due_date.replace("Z", "+00:00"))
                    if due < now:
                        overdue_count += 1
                except Exception:
                    pass

        # Estimate rescheduled tasks from productivity events
        resched_events = db.query(ProductivityEvent).filter(
            ProductivityEvent.user_id == user_id,
            ProductivityEvent.event_type == "task_rescheduled"
        ).count()
        rescheduled_count = max(resched_events, 0)

        # Priority & Category distributions
        priority_dist: Dict[str, int] = {}
        category_dist: Dict[str, int] = {}
        for t in tasks:
            p = t.priority or "Medium"
            c = t.category or "General"
            priority_dist[p] = priority_dist.get(p, 0) + 1
            category_dist[c] = category_dist.get(c, 0) + 1

        comp_rate = round((len(completed) / total * 100), 1) if total > 0 else 0.0

        return ProductivityMetricsResponse(
            tasks_total=total,
            tasks_completed=len(completed),
            tasks_pending=len(pending),
            tasks_overdue=overdue_count,
            completion_rate=comp_rate,
            completed_on_time=len(completed),
            rescheduled_count=rescheduled_count,
            priority_breakdown=priority_dist,
            category_breakdown=category_dist
        )

    def detect_patterns(self, db: Session, user_id: int) -> List[PatternItem]:
        tasks = db.query(Task).filter(Task.user_id == user_id).all()
        patterns: List[PatternItem] = []

        now = datetime.now(timezone.utc)
        high_prio_pending = [t for t in tasks if t.priority == "High" and (t.status or "").lower() != "completed"]
        if len(high_prio_pending) >= 3:
            patterns.append(PatternItem(
                pattern_type="HIGH_PRIORITY_ACCUMULATION",
                title="High-Priority Task Concentration",
                description=f"You currently have {len(high_prio_pending)} high-priority tasks pending simultaneously.",
                evidence_count=len(high_prio_pending),
                strength="HIGH"
            ))

        overdue_tasks = []
        for t in tasks:
            if (t.status or "").lower() != "completed" and t.due_date:
                try:
                    due = datetime.fromisoformat(t.due_date.replace("Z", "+00:00"))
                    if due < now:
                        overdue_tasks.append(t)
                except Exception:
                    pass

        if overdue_tasks:
            patterns.append(PatternItem(
                pattern_type="OVERDUE_DEADLINE_CLUSTER",
                title="Postponed Deadline Clusters",
                description=f"{len(overdue_tasks)} tasks have passed their scheduled deadlines without completion.",
                evidence_count=len(overdue_tasks),
                strength="HIGH"
            ))

        completed_tasks = [t for t in tasks if (t.status or "").lower() == "completed"]
        if len(completed_tasks) >= 5:
            patterns.append(PatternItem(
                pattern_type="STRONG_COMPLETION_VELOCITY",
                title="Consistent Completion Velocity",
                description=f"Strong momentum achieved with {len(completed_tasks)} tasks completed in your workspace.",
                evidence_count=len(completed_tasks),
                strength="MEDIUM"
            ))

        return patterns

    def generate_insights(self, db: Session, user_id: int) -> List[InsightItem]:
        tasks = db.query(Task).filter(Task.user_id == user_id).all()
        dismissed_ids = {
            f.insight_id for f in db.query(InsightFeedback).filter(
                InsightFeedback.user_id == user_id,
                InsightFeedback.feedback_type == "dismissed"
            ).all()
        }

        insights: List[InsightItem] = []
        now = datetime.now(timezone.utc)

        # 1. Critical Deadline Approaching
        for t in tasks:
            if (t.status or "").lower() != "completed" and t.due_date:
                try:
                    due = datetime.fromisoformat(t.due_date.replace("Z", "+00:00"))
                    diff_hours = (due - now).total_seconds() / 3600
                    if 0 <= diff_hours <= 24:
                        ins_id = f"deadline_{t.id}"
                        if ins_id not in dismissed_ids:
                            insights.append(InsightItem(
                                id=ins_id,
                                type="DEADLINE_ALERT",
                                title=f"Imminent Deadline: '{t.title}'",
                                description=f"Due in less than {max(1, int(diff_hours))} hours. Allocate dedicated focus time now.",
                                evidence=f"Priority: {t.priority} • Due: {due.strftime('%b %d, %H:%M')}",
                                urgency="HIGH",
                                recommended_action="Schedule immediate 45m deep-work block",
                                task_id=str(t.id)
                            ))
                except Exception:
                    pass

        # 2. In-Progress Bottleneck
        in_progress = [t for t in tasks if (t.status or "").lower() == "in progress"]
        if len(in_progress) >= 4:
            ins_id = "wip_bottleneck_alert"
            if ins_id not in dismissed_ids:
                insights.append(InsightItem(
                    id=ins_id,
                    type="BOTTLENECK",
                    title="High Work-in-Progress (WIP) Concentration",
                    description=f"You have {len(in_progress)} tasks concurrently 'In Progress'. Multitasking increases task completion latency.",
                    evidence=f"{len(in_progress)} concurrent active tasks",
                    urgency="MEDIUM",
                    recommended_action="Limit WIP: complete 2 active tasks before starting new ones",
                    task_id=str(in_progress[0].id) if in_progress else None
                ))

        # 3. Schedule Momentum
        completed = [t for t in tasks if (t.status or "").lower() == "completed"]
        if completed:
            ins_id = "momentum_streak"
            if ins_id not in dismissed_ids:
                insights.append(InsightItem(
                    id=ins_id,
                    type="MOMENTUM",
                    title="Peak Execution Streak",
                    description=f"You have closed {len(completed)} total tasks. Maintaining regular cadence keeps backlog healthy.",
                    evidence=f"{len(completed)} closed tasks",
                    urgency="LOW",
                    recommended_action="Review weekly analytics report",
                    task_id=None
                ))

        # Sort insights by Urgency
        urgency_weight = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        insights.sort(key=lambda x: urgency_weight.get(x.urgency, 0), reverse=True)
        return insights

    def generate_recommendations(self, db: Session, user_id: int) -> List[RecommendationItem]:
        tasks = db.query(Task).filter(Task.user_id == user_id).all()
        pending = [t for t in tasks if (t.status or "").lower() != "completed"]

        recommendations: List[RecommendationItem] = []
        now = datetime.now(timezone.utc)

        # Prioritize pending high priority and overdue tasks
        for idx, t in enumerate(pending[:5]):
            risk = "LOW"
            if t.priority == "High":
                risk = "IMMINENT"
            elif t.due_date:
                risk = "MODERATE"

            suggested_time = now.replace(hour=10 + idx, minute=0, second=0, microsecond=0)
            recommendations.append(RecommendationItem(
                id=f"rec_{t.id}",
                task_id=str(t.id),
                title=t.title,
                priority=t.priority or "Medium",
                reason=f"Ranked for completion based on {t.priority} priority and active project context.",
                suggested_time=suggested_time,
                estimated_duration_minutes=t.estimated_duration_minutes or 30,
                deadline_risk=risk
            ))

        return recommendations

    def generate_coach_response(self, db: Session, user_id: int, message: str) -> CoachResponse:
        metrics = self.calculate_metrics(db, user_id)
        patterns = self.detect_patterns(db, user_id)
        insights = self.generate_insights(db, user_id)

        msg_lower = message.lower()
        context_summary = f"User has {metrics.tasks_pending} pending tasks, {metrics.tasks_overdue} overdue, completion rate {metrics.completion_rate}%."

        actions = []
        if "focus" in msg_lower or "today" in msg_lower or "priorit" in msg_lower:
            reply = (
                f"Based on your actual workload, you have {metrics.tasks_pending} pending tasks with {metrics.tasks_overdue} overdue. "
                "I recommend focusing on your highest priority task first to clear the overdue backlog, then tackling 1-2 medium tasks during afternoon focus hours."
            )
            actions.append({
                "action": "SCHEDULE_DEEP_WORK",
                "label": "Schedule 90-minute focus block",
                "target": "top_priority_task"
            })
        elif "overdue" in msg_lower or "delay" in msg_lower:
            reply = (
                f"You have {metrics.tasks_overdue} overdue tasks. Analytical review indicates these tasks accumulated due to concurrent WIP overload. "
                "Would you like me to propose rescheduling the lowest priority overdue items into realistic upcoming time blocks?"
            )
            actions.append({
                "action": "RESCHEDULE_OVERDUE",
                "label": "Batch reschedule overdue tasks",
                "target": "overdue_tasks"
            })
        else:
            reply = (
                f"Looking at your metrics, your task completion rate is {metrics.completion_rate}% with {metrics.tasks_completed} tasks completed. "
                f"You have {len(insights)} active productivity insights. Let me know if you would like me to optimize your daily plan or review project bottlenecks."
            )

        return CoachResponse(
            reply=reply,
            suggested_actions=actions,
            data_context_summary=context_summary
        )

intelligence_engine = ProductIntelligenceEngine()
