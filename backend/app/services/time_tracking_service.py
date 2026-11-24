"""
Time Tracking & Timesheets Core Service Engine (Module B48).
Provides comprehensive business logic for active timers, manual time entries,
timesheet aggregation, approval workflows, reporting, and module integrations.
"""

from datetime import datetime, timezone, timedelta
import json
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.task import Task
from app.models.notification import Notification
from app.models.time_tracking import (
    TimeEntry,
    ActiveTimer,
    Timesheet,
    TimesheetApproval,
    TimeTrackingSettings,
    TimeEntryAuditLog,
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def parse_iso_datetime(dt_val) -> Optional[datetime]:
    if not dt_val:
        return None
    if isinstance(dt_val, datetime):
        return dt_val if dt_val.tzinfo else dt_val.replace(tzinfo=timezone.utc)
    try:
        clean_str = str(dt_val).replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        try:
            dt = datetime.strptime(str(dt_val).split("T")[0], "%Y-%m-%d")
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None

def format_duration_seconds(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s"


class TimeTrackingService:
    def get_or_create_settings(self, db: Session, user: User) -> TimeTrackingSettings:
        org_id = getattr(user, "organization_id", None)
        query = db.query(TimeTrackingSettings)
        if org_id:
            s = query.filter(TimeTrackingSettings.organization_id == org_id).first()
        else:
            s = query.filter(TimeTrackingSettings.user_id == user.id).first()

        if not s:
            s = TimeTrackingSettings(
                organization_id=org_id,
                user_id=user.id,
                default_daily_hours=8.0,
                default_weekly_hours=40.0,
                allow_manual_entry=True,
                allow_overlapping_entries=False,
                require_timesheet_approval=True,
                default_billable=True,
                default_hourly_rate=75.0,
                max_entry_duration_hours=24.0,
                submission_deadline_day="MONDAY",
                settings_json="{}",
                updated_at=utc_now(),
            )
            db.add(s)
            db.commit()
            db.refresh(s)
        return s

    # =========================================================================
    # 1. TIMER ENGINE
    # =========================================================================

    def start_timer(
        self,
        db: Session,
        user: User,
        project_id: Optional[int] = None,
        task_id: Optional[str] = None,
        description: Optional[str] = None,
        billable: bool = True,
    ) -> Dict[str, Any]:
        now = utc_now()
        org_id = getattr(user, "organization_id", None)

        # Check existing active timer
        timer = db.query(ActiveTimer).filter(ActiveTimer.user_id == user.id).first()
        if timer:
            # If already running for same task/project, return existing
            if timer.task_id == task_id and timer.project_id == project_id and timer.status == "RUNNING":
                return self.serialize_active_timer(timer)
            # If switching tasks, automatically stop previous timer and save entry
            self.stop_timer(db, user)

        # Validate task and project
        if task_id and not project_id:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task and task.project_id:
                project_id = task.project_id

        timer = ActiveTimer(
            organization_id=org_id,
            user_id=user.id,
            project_id=project_id,
            task_id=task_id,
            started_at=now,
            last_resumed_at=now,
            accumulated_seconds=0,
            status="RUNNING",
            description=description,
            billable=billable,
            created_at=now,
            updated_at=now,
        )
        db.add(timer)
        db.commit()
        db.refresh(timer)
        return self.serialize_active_timer(timer)

    def pause_timer(self, db: Session, user: User) -> Optional[Dict[str, Any]]:
        timer = db.query(ActiveTimer).filter(ActiveTimer.user_id == user.id).first()
        if not timer or timer.status == "PAUSED":
            return self.serialize_active_timer(timer) if timer else None

        now = utc_now()
        elapsed = int((now - timer.last_resumed_at.replace(tzinfo=timezone.utc)).total_seconds())
        timer.accumulated_seconds += max(0, elapsed)
        timer.status = "PAUSED"
        timer.updated_at = now
        db.commit()
        db.refresh(timer)
        return self.serialize_active_timer(timer)

    def resume_timer(self, db: Session, user: User) -> Optional[Dict[str, Any]]:
        timer = db.query(ActiveTimer).filter(ActiveTimer.user_id == user.id).first()
        if not timer:
            return None
        if timer.status == "RUNNING":
            return self.serialize_active_timer(timer)

        now = utc_now()
        timer.last_resumed_at = now
        timer.status = "RUNNING"
        timer.updated_at = now
        db.commit()
        db.refresh(timer)
        return self.serialize_active_timer(timer)

    def stop_timer(self, db: Session, user: User) -> Optional[TimeEntry]:
        timer = db.query(ActiveTimer).filter(ActiveTimer.user_id == user.id).first()
        if not timer:
            return None

        now = utc_now()
        total_seconds = timer.accumulated_seconds
        if timer.status == "RUNNING":
            elapsed = int((now - timer.last_resumed_at.replace(tzinfo=timezone.utc)).total_seconds())
            total_seconds += max(0, elapsed)

        # Minimum duration: 1 second
        duration_seconds = max(1, total_seconds)

        # Hourly rate calculation
        settings = self.get_or_create_settings(db, user)
        rate = settings.default_hourly_rate if timer.billable else 0.0
        amount = round((duration_seconds / 3600.0) * rate, 2) if timer.billable else 0.0

        # Create TimeEntry
        entry = TimeEntry(
            organization_id=timer.organization_id,
            user_id=user.id,
            project_id=timer.project_id,
            task_id=timer.task_id,
            description=timer.description,
            start_time=timer.started_at,
            end_time=now,
            duration_seconds=duration_seconds,
            billable=timer.billable,
            hourly_rate=rate,
            billable_amount=amount,
            entry_source="TIMER",
            approval_status="DRAFT",
            created_at=now,
            updated_at=now,
        )
        db.add(entry)

        # Update Task actual_minutes directly
        if timer.task_id:
            task = db.query(Task).filter(Task.id == timer.task_id).first()
            if task:
                minutes_added = max(1, duration_seconds // 60)
                task.actual_minutes = (task.actual_minutes or 0) + minutes_added
                task.updated_at = now

        # Delete active timer
        db.delete(timer)
        db.commit()
        db.refresh(entry)
        return entry

    def cancel_timer(self, db: Session, user: User) -> bool:
        timer = db.query(ActiveTimer).filter(ActiveTimer.user_id == user.id).first()
        if not timer:
            return False
        db.delete(timer)
        db.commit()
        return True

    def get_active_timer(self, db: Session, user: User) -> Optional[Dict[str, Any]]:
        timer = db.query(ActiveTimer).filter(ActiveTimer.user_id == user.id).first()
        if not timer:
            return None
        return self.serialize_active_timer(timer)

    def serialize_active_timer(self, timer: ActiveTimer) -> Dict[str, Any]:
        now = utc_now()
        elapsed = timer.accumulated_seconds
        if timer.status == "RUNNING":
            curr_elapsed = int((now - timer.last_resumed_at.replace(tzinfo=timezone.utc)).total_seconds())
            elapsed += max(0, curr_elapsed)

        return {
            "id": timer.id,
            "user_id": timer.user_id,
            "project_id": timer.project_id,
            "project_name": timer.project.name if timer.project else None,
            "task_id": timer.task_id,
            "task_title": timer.task.title if timer.task else None,
            "started_at": timer.started_at.isoformat(),
            "last_resumed_at": timer.last_resumed_at.isoformat(),
            "accumulated_seconds": timer.accumulated_seconds,
            "elapsed_seconds": elapsed,
            "status": timer.status,
            "description": timer.description,
            "billable": timer.billable,
        }

    # =========================================================================
    # 2. MANUAL TIME ENTRY
    # =========================================================================

    def create_manual_entry(
        self, db: Session, user: User, data: Dict[str, Any]
    ) -> TimeEntry:
        now = utc_now()
        org_id = getattr(user, "organization_id", None)
        settings = self.get_or_create_settings(db, user)

        start_time = parse_iso_datetime(data["start_time"]) or now
        end_time = parse_iso_datetime(data.get("end_time"))
        duration_sec = data.get("duration_seconds")

        if not duration_sec:
            if end_time and end_time > start_time:
                duration_sec = int((end_time - start_time).total_seconds())
            else:
                duration_sec = 3600  # default 1h
        if not end_time:
            end_time = start_time + timedelta(seconds=duration_sec)

        # Enforce max duration limit
        max_sec = int((settings.max_entry_duration_hours or 24.0) * 3600)
        if duration_sec > max_sec:
            duration_sec = max_sec

        billable = data.get("billable", settings.default_billable)
        rate = data.get("hourly_rate")
        if rate is None:
            rate = settings.default_hourly_rate if billable else 0.0
        amount = round((duration_sec / 3600.0) * rate, 2) if billable else 0.0

        project_id = data.get("project_id")
        task_id = data.get("task_id")
        if task_id and not project_id:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task and task.project_id:
                project_id = task.project_id

        entry = TimeEntry(
            organization_id=org_id,
            user_id=user.id,
            project_id=project_id,
            task_id=task_id,
            description=data.get("description"),
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_sec,
            billable=billable,
            hourly_rate=rate,
            billable_amount=amount,
            entry_source="MANUAL",
            approval_status="DRAFT",
            created_at=now,
            updated_at=now,
        )
        db.add(entry)

        # Update Task actual effort
        if task_id:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                minutes = max(1, duration_sec // 60)
                task.actual_minutes = (task.actual_minutes or 0) + minutes
                task.updated_at = now

        # Audit Log
        audit = TimeEntryAuditLog(
            time_entry_id=entry.id,
            user_id=user.id,
            action="CREATED",
            changes_json=json.dumps({"source": "MANUAL", "duration": duration_sec}),
            timestamp=now,
        )
        db.add(audit)

        db.commit()
        db.refresh(entry)
        return entry

    def update_entry(
        self, db: Session, user: User, entry_id: int, data: Dict[str, Any]
    ) -> Optional[TimeEntry]:
        entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
        if not entry:
            return None

        # Check permission: owner or admin
        if entry.user_id != user.id and (getattr(user, "role", "") or "").upper() not in ("ADMIN", "OWNER"):
            return None

        # Prevent editing approved entries unless reopened
        if entry.approval_status == "APPROVED":
            return None

        now = utc_now()
        changes = {}

        if "description" in data and data["description"] is not None:
            changes["description"] = (entry.description, data["description"])
            entry.description = data["description"]

        if "duration_seconds" in data and data["duration_seconds"] is not None:
            old_dur = entry.duration_seconds
            new_dur = max(1, data["duration_seconds"])
            changes["duration_seconds"] = (old_dur, new_dur)
            entry.duration_seconds = new_dur
            if entry.billable and entry.hourly_rate:
                entry.billable_amount = round((new_dur / 3600.0) * entry.hourly_rate, 2)
            # Rebalance task actual minutes
            if entry.task_id:
                task = db.query(Task).filter(Task.id == entry.task_id).first()
                if task:
                    delta_min = (new_dur - old_dur) // 60
                    task.actual_minutes = max(0, (task.actual_minutes or 0) + delta_min)

        if "billable" in data and data["billable"] is not None:
            entry.billable = data["billable"]
            if not entry.billable:
                entry.billable_amount = 0.0

        if "hourly_rate" in data and data["hourly_rate"] is not None:
            entry.hourly_rate = data["hourly_rate"]
            if entry.billable:
                entry.billable_amount = round((entry.duration_seconds / 3600.0) * entry.hourly_rate, 2)

        entry.updated_at = now

        audit = TimeEntryAuditLog(
            time_entry_id=entry.id,
            user_id=user.id,
            action="UPDATED",
            changes_json=json.dumps(str(changes)),
            timestamp=now,
        )
        db.add(audit)

        db.commit()
        db.refresh(entry)
        return entry

    def delete_entry(self, db: Session, user: User, entry_id: int) -> bool:
        entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
        if not entry:
            return False

        if entry.user_id != user.id and (getattr(user, "role", "") or "").upper() not in ("ADMIN", "OWNER"):
            return False

        if entry.approval_status == "APPROVED":
            return False

        # Adjust task actual minutes
        if entry.task_id:
            task = db.query(Task).filter(Task.id == entry.task_id).first()
            if task:
                minutes = entry.duration_seconds // 60
                task.actual_minutes = max(0, (task.actual_minutes or 0) - minutes)

        audit = TimeEntryAuditLog(
            time_entry_id=entry.id,
            user_id=user.id,
            action="DELETED",
            changes_json=json.dumps({"deleted_duration": entry.duration_seconds}),
            timestamp=utc_now(),
        )
        db.add(audit)

        db.delete(entry)
        db.commit()
        return True

    def get_entries(
        self,
        db: Session,
        user: User,
        project_id: Optional[int] = None,
        task_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        approval_status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query = db.query(TimeEntry)

        # If ordinary member, only own entries; if admin/manager, org entries
        role_upper = (getattr(user, "role", "") or "").upper()
        if role_upper not in ("ADMIN", "OWNER", "MANAGER"):
            query = query.filter(TimeEntry.user_id == user.id)
        else:
            org_id = getattr(user, "organization_id", None)
            if org_id:
                query = query.filter(TimeEntry.organization_id == org_id)

        if project_id:
            query = query.filter(TimeEntry.project_id == project_id)
        if task_id:
            query = query.filter(TimeEntry.task_id == task_id)
        if approval_status:
            query = query.filter(TimeEntry.approval_status == approval_status.upper())
        if start_date:
            dt_s = parse_iso_datetime(start_date)
            if dt_s:
                query = query.filter(TimeEntry.start_time >= dt_s)
        if end_date:
            dt_e = parse_iso_datetime(end_date)
            if dt_e:
                query = query.filter(TimeEntry.start_time <= dt_e)

        entries = query.order_by(desc(TimeEntry.start_time)).offset(offset).limit(limit).all()
        return [self.serialize_time_entry(e) for e in entries]

    def serialize_time_entry(self, e: TimeEntry) -> Dict[str, Any]:
        return {
            "id": e.id,
            "user_id": e.user_id,
            "user_name": e.user.name if e.user else None,
            "project_id": e.project_id,
            "project_name": e.project.name if e.project else None,
            "task_id": e.task_id,
            "task_title": e.task.title if e.task else None,
            "timesheet_id": e.timesheet_id,
            "description": e.description,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat() if e.end_time else None,
            "duration_seconds": e.duration_seconds,
            "duration_formatted": format_duration_seconds(e.duration_seconds),
            "billable": e.billable,
            "hourly_rate": e.hourly_rate,
            "billable_amount": e.billable_amount,
            "entry_source": e.entry_source,
            "approval_status": e.approval_status,
            "created_at": e.created_at.isoformat(),
        }

    # =========================================================================
    # 3. TIMESHEET MANAGEMENT & APPROVAL WORKFLOW
    # =========================================================================

    def get_or_create_timesheet(
        self, db: Session, user: User, period_start: str, period_end: str
    ) -> Timesheet:
        now = utc_now()
        org_id = getattr(user, "organization_id", None)
        dt_start = parse_iso_datetime(period_start) or (now - timedelta(days=7))
        dt_end = parse_iso_datetime(period_end) or now

        ts = db.query(Timesheet).filter(
            Timesheet.user_id == user.id,
            Timesheet.period_start == dt_start,
            Timesheet.period_end == dt_end,
        ).first()

        if not ts:
            ts = Timesheet(
                organization_id=org_id,
                user_id=user.id,
                period_start=dt_start,
                period_end=dt_end,
                status="DRAFT",
                created_at=now,
                updated_at=now,
            )
            db.add(ts)
            db.commit()
            db.refresh(ts)

        self.recalculate_timesheet_totals(db, ts)
        return ts

    def recalculate_timesheet_totals(self, db: Session, ts: Timesheet):
        # Fetch all time entries within period for user
        entries = db.query(TimeEntry).filter(
            TimeEntry.user_id == ts.user_id,
            TimeEntry.start_time >= ts.period_start,
            TimeEntry.start_time <= ts.period_end,
        ).all()

        total = sum(e.duration_seconds for e in entries)
        billable = sum(e.duration_seconds for e in entries if e.billable)
        non_billable = total - billable

        ts.total_seconds = total
        ts.billable_seconds = billable
        ts.non_billable_seconds = non_billable
        ts.updated_at = utc_now()

        # Associate unassociated entries with this timesheet
        for e in entries:
            if not e.timesheet_id:
                e.timesheet_id = ts.id
        db.commit()

    def submit_timesheet(
        self, db: Session, user: User, timesheet_id: int
    ) -> Optional[Timesheet]:
        ts = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
        if not ts or ts.user_id != user.id:
            return None
        if ts.status not in ("DRAFT", "REJECTED", "REOPENED"):
            return ts

        now = utc_now()
        self.recalculate_timesheet_totals(db, ts)
        ts.status = "SUBMITTED"
        ts.submitted_at = now
        ts.updated_at = now

        # Update linked time entries
        entries = db.query(TimeEntry).filter(TimeEntry.timesheet_id == ts.id).all()
        for e in entries:
            e.approval_status = "SUBMITTED"
            e.updated_at = now

        # Create manager notification
        org_id = getattr(user, "organization_id", None)
        admin_user = (
            db.query(User).filter(User.organization_id == org_id, User.role.in_(["Admin", "Owner", "Manager"])).first()
            if org_id else None
        )
        if admin_user and admin_user.id != user.id:
            notif = Notification(
                user_id=admin_user.id,
                organization_id=org_id,
                category="PROJECT",
                type="TIMESHEET_SUBMITTED",
                title=f"Timesheet submitted by {user.name or user.email}",
                message=f"{round(ts.total_seconds / 3600.0, 1)} hours recorded for approval ({ts.period_start.strftime('%b %d')} - {ts.period_end.strftime('%b %d')}).",
                priority="NORMAL",
                status="SENT",
                created_at=now,
                metadata_json=json.dumps({"timesheet_id": ts.id, "target_tab": "time-tracking"})
            )
            db.add(notif)

        db.commit()
        db.refresh(ts)
        return ts

    def withdraw_timesheet(
        self, db: Session, user: User, timesheet_id: int
    ) -> Optional[Timesheet]:
        ts = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
        if not ts or ts.user_id != user.id or ts.status != "SUBMITTED":
            return None

        now = utc_now()
        ts.status = "DRAFT"
        ts.updated_at = now

        entries = db.query(TimeEntry).filter(TimeEntry.timesheet_id == ts.id).all()
        for e in entries:
            e.approval_status = "DRAFT"
            e.updated_at = now

        db.commit()
        db.refresh(ts)
        return ts

    def review_timesheet(
        self,
        db: Session,
        reviewer: User,
        timesheet_id: int,
        decision: str,  # APPROVED, REJECTED, REOPENED
        comments: Optional[str] = None,
    ) -> Optional[Timesheet]:
        ts = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
        if not ts:
            return None

        now = utc_now()
        ts.status = decision
        ts.reviewed_at = now
        ts.reviewer_id = reviewer.id
        ts.review_comments = comments
        ts.updated_at = now

        # Update entries
        entry_status = "APPROVED" if decision == "APPROVED" else "REJECTED" if decision == "REJECTED" else "DRAFT"
        entries = db.query(TimeEntry).filter(TimeEntry.timesheet_id == ts.id).all()
        for e in entries:
            e.approval_status = entry_status
            e.updated_at = now

        # Record Approval Log
        appr = TimesheetApproval(
            timesheet_id=ts.id,
            reviewer_id=reviewer.id,
            decision=decision,
            review_comments=comments,
            created_at=now,
        )
        db.add(appr)

        # Notify Timesheet Owner
        notif = Notification(
            user_id=ts.user_id,
            organization_id=ts.organization_id,
            category="PROJECT",
            type=f"TIMESHEET_{decision}",
            title=f"Timesheet {decision.lower()}: {ts.period_start.strftime('%b %d')} - {ts.period_end.strftime('%b %d')}",
            message=comments or f"Your timesheet of {round(ts.total_seconds / 3600.0, 1)} hours was {decision.lower()}.",
            priority="HIGH" if decision == "REJECTED" else "NORMAL",
            status="SENT",
            created_at=now,
            metadata_json=json.dumps({"timesheet_id": ts.id, "target_tab": "time-tracking"})
        )
        db.add(notif)

        db.commit()
        db.refresh(ts)
        return ts

    def get_timesheets(
        self, db: Session, user: User, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = db.query(Timesheet)
        role_upper = (getattr(user, "role", "") or "").upper()
        if role_upper not in ("ADMIN", "OWNER", "MANAGER"):
            query = query.filter(Timesheet.user_id == user.id)
        else:
            org_id = getattr(user, "organization_id", None)
            if org_id:
                query = query.filter(Timesheet.organization_id == org_id)

        if status:
            query = query.filter(Timesheet.status == status.upper())

        timesheets = query.order_by(desc(Timesheet.period_start)).all()
        return [self.serialize_timesheet(t) for t in timesheets]

    def get_timesheet_detail(
        self, db: Session, timesheet_id: int, user: User
    ) -> Optional[Dict[str, Any]]:
        ts = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
        if not ts:
            return None

        # Recalculate totals
        self.recalculate_timesheet_totals(db, ts)

        entries = db.query(TimeEntry).filter(TimeEntry.timesheet_id == ts.id).all()
        approvals = db.query(TimesheetApproval).filter(TimesheetApproval.timesheet_id == ts.id).order_by(TimesheetApproval.created_at).all()

        data = self.serialize_timesheet(ts)
        data["time_entries"] = [self.serialize_time_entry(e) for e in entries]
        data["approvals"] = [
            {
                "id": a.id,
                "reviewer_id": a.reviewer_id,
                "reviewer_name": a.reviewer.name if a.reviewer else None,
                "decision": a.decision,
                "review_comments": a.review_comments,
                "created_at": a.created_at.isoformat(),
            }
            for a in approvals
        ]
        return data

    def serialize_timesheet(self, t: Timesheet) -> Dict[str, Any]:
        return {
            "id": t.id,
            "user_id": t.user_id,
            "user_name": t.user.name if t.user else None,
            "user_email": t.user.email if t.user else None,
            "period_start": t.period_start.isoformat(),
            "period_end": t.period_end.isoformat(),
            "total_seconds": t.total_seconds,
            "total_hours": round(t.total_seconds / 3600.0, 1),
            "billable_seconds": t.billable_seconds,
            "billable_hours": round(t.billable_seconds / 3600.0, 1),
            "non_billable_seconds": t.non_billable_seconds,
            "non_billable_hours": round(t.non_billable_seconds / 3600.0, 1),
            "status": t.status,
            "submitted_at": t.submitted_at.isoformat() if t.submitted_at else None,
            "reviewed_at": t.reviewed_at.isoformat() if t.reviewed_at else None,
            "reviewer_id": t.reviewer_id,
            "reviewer_name": t.reviewer.name if t.reviewer else None,
            "review_comments": t.review_comments,
            "created_at": t.created_at.isoformat(),
            "entries_count": len(t.time_entries) if t.time_entries else 0,
        }

    # =========================================================================
    # 4. REPORTING & SUMMARY
    # =========================================================================

    def get_summary(self, db: Session, user: User) -> Dict[str, Any]:
        now = utc_now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        # Today's entries
        today_entries = db.query(TimeEntry).filter(
            TimeEntry.user_id == user.id,
            TimeEntry.start_time >= today_start
        ).all()
        today_sec = sum(e.duration_seconds for e in today_entries)

        # This week's entries
        week_entries = db.query(TimeEntry).filter(
            TimeEntry.user_id == user.id,
            TimeEntry.start_time >= week_start
        ).all()
        week_sec = sum(e.duration_seconds for e in week_entries)
        billable_sec = sum(e.duration_seconds for e in week_entries if e.billable)

        # Active timer
        active = self.get_active_timer(db, user)

        # Recent entries
        recent = db.query(TimeEntry).filter(
            TimeEntry.user_id == user.id
        ).order_by(desc(TimeEntry.start_time)).limit(5).all()

        # Pending timesheets
        pending_count = db.query(Timesheet).filter(
            Timesheet.user_id == user.id,
            Timesheet.status.in_(["DRAFT", "SUBMITTED"])
        ).count()

        return {
            "today_seconds": today_sec,
            "today_hours": round(today_sec / 3600.0, 1),
            "this_week_seconds": week_sec,
            "this_week_hours": round(week_sec / 3600.0, 1),
            "billable_seconds": billable_sec,
            "billable_hours": round(billable_sec / 3600.0, 1),
            "non_billable_seconds": week_sec - billable_sec,
            "non_billable_hours": round((week_sec - billable_sec) / 3600.0, 1),
            "active_timer": active,
            "recent_entries": [self.serialize_time_entry(e) for e in recent],
            "pending_timesheets_count": pending_count,
        }

    def get_project_reports(self, db: Session, user: User) -> List[Dict[str, Any]]:
        entries = db.query(TimeEntry).all()
        by_project: Dict[Optional[int], List[TimeEntry]] = {}
        for e in entries:
            by_project.setdefault(e.project_id, []).append(e)

        results = []
        for p_id, p_entries in by_project.items():
            project = db.query(Project).filter(Project.id == p_id).first() if p_id else None
            tot_sec = sum(e.duration_seconds for e in p_entries)
            bill_sec = sum(e.duration_seconds for e in p_entries if e.billable)
            amount = sum(e.billable_amount or 0.0 for e in p_entries)
            results.append({
                "project_id": p_id,
                "project_name": project.name if project else "General Work / Unassigned",
                "total_seconds": tot_sec,
                "total_hours": round(tot_sec / 3600.0, 1),
                "billable_hours": round(bill_sec / 3600.0, 1),
                "billable_amount": round(amount, 2),
                "entries_count": len(p_entries),
            })
        return sorted(results, key=lambda x: x["total_seconds"], reverse=True)

    def get_user_reports(self, db: Session, user: User) -> List[Dict[str, Any]]:
        entries = db.query(TimeEntry).all()
        by_user: Dict[int, List[TimeEntry]] = {}
        for e in entries:
            by_user.setdefault(e.user_id, []).append(e)

        results = []
        for u_id, u_entries in by_user.items():
            u = db.query(User).filter(User.id == u_id).first()
            tot_sec = sum(e.duration_seconds for e in u_entries)
            bill_sec = sum(e.duration_seconds for e in u_entries if e.billable)
            results.append({
                "user_id": u_id,
                "user_name": u.name if u else "Unknown User",
                "user_email": u.email if u else "unknown@focusboard.io",
                "total_seconds": tot_sec,
                "total_hours": round(tot_sec / 3600.0, 1),
                "billable_hours": round(bill_sec / 3600.0, 1),
                "entries_count": len(u_entries),
            })
        return sorted(results, key=lambda x: x["total_seconds"], reverse=True)

    def get_billable_report(self, db: Session, user: User) -> Dict[str, Any]:
        proj_reports = self.get_project_reports(db, user)
        total_bill_hours = sum(p["billable_hours"] for p in proj_reports)
        total_non_bill_hours = sum(p["total_hours"] - p["billable_hours"] for p in proj_reports)
        total_amount = sum(p["billable_amount"] for p in proj_reports)

        return {
            "total_billable_hours": round(total_bill_hours, 1),
            "total_non_billable_hours": round(total_non_bill_hours, 1),
            "total_billable_amount": round(total_amount, 2),
            "currency": "USD",
            "projects_breakdown": proj_reports,
        }

    def serialize_settings(self, s: TimeTrackingSettings) -> Dict[str, Any]:
        return {
            "default_daily_hours": s.default_daily_hours,
            "default_weekly_hours": s.default_weekly_hours,
            "allow_manual_entry": s.allow_manual_entry,
            "allow_overlapping_entries": s.allow_overlapping_entries,
            "require_timesheet_approval": s.require_timesheet_approval,
            "default_billable": s.default_billable,
            "default_hourly_rate": s.default_hourly_rate,
            "max_entry_duration_hours": s.max_entry_duration_hours,
            "submission_deadline_day": s.submission_deadline_day,
            "updated_at": s.updated_at.isoformat() if s.updated_at else utc_now().isoformat(),
        }

    def update_settings(self, db: Session, user: User, data: Dict[str, Any]) -> TimeTrackingSettings:
        s = self.get_or_create_settings(db, user)
        for k, v in data.items():
            if hasattr(s, k) and v is not None:
                setattr(s, k, v)
        s.updated_at = utc_now()
        db.commit()
        db.refresh(s)
        return s


time_tracking_service = TimeTrackingService()
