import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.reminder import TaskRecurrenceRule
from app.models.task import Task
from app.models.user import User
from app.schemas.reminder import (
    RecurrenceRuleCreate,
    RecurrenceRuleUpdate,
    RecurrenceRuleResponse,
)

def calculate_next_run(base_dt: datetime, frequency: str, interval: int) -> datetime:
    """Calculate the next execution timestamp based on pattern."""
    freq = frequency.upper()
    if freq == "DAILY":
        return base_dt + timedelta(days=interval)
    elif freq == "WEEKLY":
        return base_dt + timedelta(weeks=interval)
    elif freq == "MONTHLY":
        # Approximate 30 days
        return base_dt + timedelta(days=30 * interval)
    elif freq == "YEARLY":
        return base_dt + timedelta(days=365 * interval)
    return base_dt + timedelta(days=interval)

class RecurrenceService:
    def set_task_recurrence(
        self,
        db: Session,
        current_user: User,
        task_id: str,
        rule_in: RecurrenceRuleCreate,
    ) -> TaskRecurrenceRule:
        """Create or update recurrence rule for a task."""
        task = db.query(Task).filter(Task.id == task_id, Task.is_deleted == False).first()
        if not task:
            raise ValueError("Task not found")

        if task.user_id != current_user.id and task.assignee_id != current_user.id:
            raise ValueError("Unauthorized to configure recurrence for this task")

        if rule_in.interval < 1:
            raise ValueError("Recurrence interval must be at least 1")

        valid_freqs = ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]
        if rule_in.frequency.upper() not in valid_freqs:
            raise ValueError(f"Invalid frequency. Must be one of {valid_freqs}")

        now_utc = datetime.now(timezone.utc)
        base_dt = task.scheduled_start or now_utc
        if base_dt.tzinfo is None:
            base_dt = base_dt.replace(tzinfo=timezone.utc)
        next_run = calculate_next_run(base_dt, rule_in.frequency, rule_in.interval)

        existing_rule = db.query(TaskRecurrenceRule).filter(TaskRecurrenceRule.task_id == task_id).first()
        if existing_rule:
            existing_rule.frequency = rule_in.frequency.upper()
            existing_rule.interval = rule_in.interval
            existing_rule.weekdays_json = json.dumps(rule_in.weekdays or [])
            existing_rule.month_day = rule_in.month_day
            existing_rule.end_date = rule_in.end_date
            existing_rule.max_occurrences = rule_in.max_occurrences
            existing_rule.next_run_at = next_run
            existing_rule.is_active = True
            rule = existing_rule
        else:
            rule = TaskRecurrenceRule(
                task_id=task_id,
                user_id=current_user.id,
                organization_id=task.organization_id or getattr(current_user, "organization_id", None),
                frequency=rule_in.frequency.upper(),
                interval=rule_in.interval,
                weekdays_json=json.dumps(rule_in.weekdays or []),
                month_day=rule_in.month_day,
                end_date=rule_in.end_date,
                max_occurrences=rule_in.max_occurrences,
                occurrences_created=0,
                next_run_at=next_run,
                is_active=True,
            )
            db.add(rule)

        db.commit()
        db.refresh(rule)
        return rule

    def get_task_recurrence(self, db: Session, current_user: User, task_id: str) -> TaskRecurrenceRule:
        """Fetch recurrence rule for a task."""
        rule = db.query(TaskRecurrenceRule).filter(TaskRecurrenceRule.task_id == task_id).first()
        if not rule:
            raise ValueError("Recurrence rule not found")
        return rule

    def delete_task_recurrence(self, db: Session, current_user: User, task_id: str) -> bool:
        """Delete recurrence rule for a task."""
        rule = self.get_task_recurrence(db, current_user, task_id)
        db.delete(rule)
        db.commit()
        return True

    def generate_next_occurrence(self, db: Session, current_user: User, task_id: str) -> Task:
        """Generate the next recurring task instance."""
        task = db.query(Task).filter(Task.id == task_id, Task.is_deleted == False).first()
        if not task:
            raise ValueError("Original task not found")

        rule = db.query(TaskRecurrenceRule).filter(TaskRecurrenceRule.task_id == task_id, TaskRecurrenceRule.is_active == True).first()
        if not rule:
            raise ValueError("No active recurrence rule for this task")

        now_utc = datetime.now(timezone.utc)
        if rule.end_date and now_utc > rule.end_date:
            rule.is_active = False
            db.commit()
            raise ValueError("Recurrence rule has expired (end_date reached)")

        if rule.max_occurrences and rule.occurrences_created >= rule.max_occurrences:
            rule.is_active = False
            db.commit()
            raise ValueError("Recurrence rule has reached maximum occurrences")

        # Create new task instance
        rule.occurrences_created += 1
        new_task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        duration = task.estimated_duration_minutes or 30
        new_start = rule.next_run_at or now_utc
        new_end = new_start + timedelta(minutes=duration)
        new_due = new_start.strftime("%Y-%m-%d")

        new_task = Task(
            id=new_task_id,
            title=f"{task.title} (Occurrence #{rule.occurrences_created})",
            description=task.description,
            category=task.category,
            status="Todo",
            priority=task.priority,
            due_date=new_due,
            start_date=new_due,
            is_all_day=task.is_all_day,
            scheduled_start=new_start,
            scheduled_end=new_end,
            estimated_duration_minutes=duration,
            user_id=task.user_id,
            organization_id=task.organization_id,
            workspace_id=task.workspace_id,
            project_id=task.project_id,
            assignee_id=task.assignee_id,
            labels_json=task.labels_json,
        )
        db.add(new_task)

        # Advance next_run_at
        rule.next_run_at = calculate_next_run(new_start, rule.frequency, rule.interval)
        if rule.max_occurrences and rule.occurrences_created >= rule.max_occurrences:
            rule.is_active = False

        db.commit()
        db.refresh(new_task)
        return new_task

recurrence_service = RecurrenceService()
