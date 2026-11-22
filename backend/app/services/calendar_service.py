from datetime import datetime, timezone, timedelta, date, time
from typing import List, Optional, Dict, Any, Tuple
try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:
    from pytz import timezone as ZoneInfo, UnknownTimeZoneError as ZoneInfoNotFoundError

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.task import Task
from app.models.project import Project
from app.models.user import User
from app.models.organization import OrganizationMember
from app.models.collaboration import WorkspaceMember
from app.schemas.calendar import (
    CalendarTaskItem,
    CalendarDataResponse,
    CalendarSummaryResponse,
    RescheduleTaskRequest,
    CalendarConflictItem,
    CalendarEventItem,
)
from app.services.google_calendar_service import calendar_service as google_calendar_service

def get_safe_timezone(tz_name: Optional[str]) -> Any:
    """Resolve standard ZoneInfo with safe fallback to UTC."""
    if not tz_name:
        return ZoneInfo("UTC")
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("UTC")

def parse_date_to_utc_bounds(dt: datetime, tz: Any) -> Tuple[datetime, datetime]:
    """Given a datetime in local timezone, return UTC start and end bounds for that calendar day."""
    if dt.tzinfo is None:
        local_dt = dt.replace(tzinfo=tz)
    else:
        local_dt = dt.astimezone(tz)
    
    start_local = datetime.combine(local_dt.date(), time.min, tzinfo=tz)
    end_local = datetime.combine(local_dt.date(), time.max, tzinfo=tz)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

class CalendarService:
    def _is_task_overdue(self, task: Task, now_utc: datetime, tz: Any) -> bool:
        """Determines if a task is overdue (excluding completed tasks)."""
        if task.status.lower() in ["completed", "done"]:
            return False

        # Check due_date
        if task.due_date:
            try:
                # Format: YYYY-MM-DD
                if len(task.due_date) == 10 and "-" in task.due_date:
                    parts = [int(p) for p in task.due_date.split("-")]
                    due_day = date(parts[0], parts[1], parts[2])
                    # End of day in user timezone converted to UTC
                    end_of_day = datetime.combine(due_day, time(23, 59, 59), tzinfo=tz).astimezone(timezone.utc)
                    if now_utc > end_of_day:
                        return True
                else:
                    # ISO format datetime string
                    iso_dt = datetime.fromisoformat(task.due_date.replace("Z", "+00:00"))
                    if iso_dt.tzinfo is None:
                        iso_dt = iso_dt.replace(tzinfo=timezone.utc)
                    if now_utc > iso_dt:
                        return True
            except Exception:
                pass

        # Check scheduled_end
        if task.scheduled_end:
            sched_end = task.scheduled_end
            if sched_end.tzinfo is None:
                sched_end = sched_end.replace(tzinfo=timezone.utc)
            if now_utc > sched_end:
                return True

        return False

    def _is_task_due_today(self, task: Task, today_start_utc: datetime, today_end_utc: datetime, today_str: str) -> bool:
        """Determines if a task is due today."""
        if task.due_date and task.due_date.startswith(today_str):
            return True
        if task.scheduled_start:
            s_start = task.scheduled_start.replace(tzinfo=timezone.utc) if task.scheduled_start.tzinfo is None else task.scheduled_start
            if today_start_utc <= s_start <= today_end_utc:
                return True
        return False

    def _map_task_to_calendar_item(self, task: Task, now_utc: datetime, tz: Any, project_map: Dict[int, Project]) -> CalendarTaskItem:
        """Convert a database Task into a CalendarTaskItem."""
        duration = task.estimated_duration_minutes or 30
        
        # Calculate start and end
        if task.scheduled_start:
            start_dt = task.scheduled_start
            end_dt = task.scheduled_end or (start_dt + timedelta(minutes=duration))
        elif task.due_date:
            try:
                if len(task.due_date) == 10:
                    parts = [int(p) for p in task.due_date.split("-")]
                    d = date(parts[0], parts[1], parts[2])
                    start_dt = datetime.combine(d, time(9, 0), tzinfo=timezone.utc)
                    end_dt = start_dt + timedelta(minutes=duration)
                else:
                    end_dt = datetime.fromisoformat(task.due_date.replace("Z", "+00:00"))
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=timezone.utc)
                    start_dt = end_dt - timedelta(minutes=duration)
            except Exception:
                start_dt = now_utc
                end_dt = now_utc + timedelta(minutes=duration)
        else:
            start_dt = task.created_at or now_utc
            end_dt = start_dt + timedelta(minutes=duration)

        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)

        is_completed = task.status.lower() in ["completed", "done"]
        is_overdue = self._is_task_overdue(task, now_utc, tz)

        proj = project_map.get(task.project_id) if task.project_id else None

        return CalendarTaskItem(
            id=f"cal-task-{task.id}",
            task_id=str(task.id),
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            category=task.category or "Design",
            start=start_dt,
            end=end_dt,
            due_date=task.due_date,
            start_date=getattr(task, "start_date", None),
            is_all_day=getattr(task, "is_all_day", False),
            duration_minutes=duration,
            is_completed=is_completed,
            is_overdue=is_overdue,
            source="focusboard",
            project_id=task.project_id,
            project_name=proj.name if proj else None,
            project_color=proj.color if proj and hasattr(proj, "color") else "#4F46E5",
            workspace_id=task.workspace_id,
            assignee_id=task.assignee_id,
            labels=task.labels if hasattr(task, "labels") else [],
        )

    def get_calendar_data(
        self,
        db: Session,
        current_user: User,
        view: str = "month",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        category: Optional[str] = None,
        tz_name: str = "UTC",
    ) -> CalendarDataResponse:
        """Fetch tasks within date range and format for month/week/day/agenda views."""
        tz = get_safe_timezone(tz_name)
        now_local = datetime.now(tz)
        now_utc = datetime.now(timezone.utc)

        # 1. Determine effective date bounds based on view
        if not start_date or not end_date:
            if view == "day":
                s_local = datetime.combine(now_local.date(), time.min, tzinfo=tz)
                e_local = datetime.combine(now_local.date(), time.max, tzinfo=tz)
            elif view == "week":
                # Week starts on Monday
                start_of_week = now_local.date() - timedelta(days=now_local.weekday())
                s_local = datetime.combine(start_of_week, time.min, tzinfo=tz)
                e_local = datetime.combine(start_of_week + timedelta(days=6), time.max, tzinfo=tz)
            elif view == "agenda":
                s_local = datetime.combine(now_local.date(), time.min, tzinfo=tz)
                e_local = datetime.combine(now_local.date() + timedelta(days=30), time.max, tzinfo=tz)
            else:  # month (default)
                first_of_month = now_local.date().replace(day=1)
                # Next month first day minus one day
                if first_of_month.month == 12:
                    next_month = date(first_of_month.year + 1, 1, 1)
                else:
                    next_month = date(first_of_month.year, first_of_month.month + 1, 1)
                last_of_month = next_month - timedelta(days=1)
                # Expand slightly to cover full calendar grid
                grid_start = first_of_month - timedelta(days=first_of_month.weekday())
                grid_end = last_of_month + timedelta(days=(6 - last_of_month.weekday()) + 7)
                s_local = datetime.combine(grid_start, time.min, tzinfo=tz)
                e_local = datetime.combine(grid_end, time.max, tzinfo=tz)
            
            start_range_utc = s_local.astimezone(timezone.utc)
            end_range_utc = e_local.astimezone(timezone.utc)
        else:
            start_range_utc = start_date.astimezone(timezone.utc) if start_date.tzinfo else start_date.replace(tzinfo=timezone.utc)
            end_range_utc = end_date.astimezone(timezone.utc) if end_date.tzinfo else end_date.replace(tzinfo=timezone.utc)

        # Today bounds in local timezone converted to UTC
        today_start_utc, today_end_utc = parse_date_to_utc_bounds(now_local, tz)
        today_str = now_local.strftime("%Y-%m-%d")

        # 2. Build tenant and filter-aware task query
        query = db.query(Task).filter(Task.is_deleted == False)

        # Tenant isolation
        if workspace_id:
            query = query.filter(Task.workspace_id == workspace_id)
        elif organization_id:
            query = query.filter(Task.organization_id == organization_id)
        else:
            # Fallback to user-accessible tasks
            query = query.filter(
                or_(
                    Task.user_id == current_user.id,
                    Task.assignee_id == current_user.id,
                )
            )

        if project_id:
            query = query.filter(Task.project_id == project_id)
        if status:
            query = query.filter(func.lower(Task.status) == status.lower())
        if priority:
            query = query.filter(func.lower(Task.priority) == priority.lower())
        if assignee_id:
            query = query.filter(Task.assignee_id == assignee_id)
        if category:
            query = query.filter(func.lower(Task.category) == category.lower())

        # Date range condition: scheduled_start between range OR due_date roughly matches
        query = query.filter(
            or_(
                and_(Task.scheduled_start >= start_range_utc, Task.scheduled_start <= end_range_utc),
                and_(Task.scheduled_end >= start_range_utc, Task.scheduled_end <= end_range_utc),
                Task.due_date.isnot(None),
            )
        )

        tasks = query.all()

        # Pre-load projects for labels & colors
        project_ids = list({t.project_id for t in tasks if t.project_id})
        project_map = {}
        if project_ids:
            projs = db.query(Project).filter(Project.id.in_(project_ids)).all()
            project_map = {p.id: p for p in projs}

        # 3. Transform and group tasks
        calendar_items: List[CalendarTaskItem] = []
        date_groups: Dict[str, List[CalendarTaskItem]] = {}

        completed_count = 0
        overdue_count = 0
        due_today_count = 0

        for t in tasks:
            item = self._map_task_to_calendar_item(t, now_utc, tz, project_map)
            
            # Filter items that fall within the view range (in local tz)
            item_local_dt = item.start.astimezone(tz)
            item_local_date_str = item_local_dt.strftime("%Y-%m-%d")

            calendar_items.append(item)

            if item.is_completed:
                completed_count += 1
            if item.is_overdue:
                overdue_count += 1
            if self._is_task_due_today(t, today_start_utc, today_end_utc, today_str):
                due_today_count += 1

            if item_local_date_str not in date_groups:
                date_groups[item_local_date_str] = []
            date_groups[item_local_date_str].append(item)

        # Sort calendar items chronologically
        calendar_items.sort(key=lambda x: x.start)

        # Fetch external Google calendar events if integrated
        external_events = []
        try:
            external_events = google_calendar_service.fetch_calendar_events(
                db, current_user.id, start_range_utc, end_range_utc
            )
            # Filter out duplicated focusboard tasks
            external_events = [e for e in external_events if e.source != "focusboard"]
        except Exception:
            pass

        return CalendarDataResponse(
            view=view,
            start_range=start_range_utc,
            end_range=end_range_utc,
            timezone=tz_name,
            total_tasks=len(calendar_items),
            completed_count=completed_count,
            overdue_count=overdue_count,
            due_today_count=due_today_count,
            tasks=calendar_items,
            external_events=external_events,
            date_groups=date_groups,
        )

    def get_calendar_summary(
        self,
        db: Session,
        current_user: User,
        workspace_id: Optional[int] = None,
        project_id: Optional[int] = None,
        tz_name: str = "UTC",
    ) -> CalendarSummaryResponse:
        """Calculate high-level calendar and deadline metrics."""
        tz = get_safe_timezone(tz_name)
        now_local = datetime.now(tz)
        now_utc = datetime.now(timezone.utc)

        today_start_utc, today_end_utc = parse_date_to_utc_bounds(now_local, tz)
        today_str = now_local.strftime("%Y-%m-%d")

        query = db.query(Task).filter(Task.is_deleted == False)
        if workspace_id:
            query = query.filter(Task.workspace_id == workspace_id)
        else:
            query = query.filter(or_(Task.user_id == current_user.id, Task.assignee_id == current_user.id))

        if project_id:
            query = query.filter(Task.project_id == project_id)

        tasks = query.all()

        total_scheduled = 0
        due_today = 0
        overdue = 0
        upcoming_7 = 0
        upcoming_30 = 0
        completed = 0
        status_counts: Dict[str, int] = {}
        priority_counts: Dict[str, int] = {}

        next_7_utc = now_utc + timedelta(days=7)
        next_30_utc = now_utc + timedelta(days=30)

        for t in tasks:
            status_lower = t.status.lower()
            status_counts[t.status] = status_counts.get(t.status, 0) + 1
            priority_counts[t.priority] = priority_counts.get(t.priority, 0) + 1

            if status_lower in ["completed", "done"]:
                completed += 1
            else:
                if self._is_task_overdue(t, now_utc, tz):
                    overdue += 1

            if t.scheduled_start or t.due_date:
                total_scheduled += 1

            if self._is_task_due_today(t, today_start_utc, today_end_utc, today_str):
                due_today += 1

            # Upcoming window checks (excluding completed)
            if status_lower not in ["completed", "done"]:
                t_dt = t.scheduled_start or None
                if not t_dt and t.due_date and len(t.due_date) == 10:
                    try:
                        p = [int(x) for x in t.due_date.split("-")]
                        t_dt = datetime(p[0], p[1], p[2], tzinfo=timezone.utc)
                    except Exception:
                        pass
                if t_dt:
                    if t_dt.tzinfo is None:
                        t_dt = t_dt.replace(tzinfo=timezone.utc)
                    if now_utc < t_dt <= next_7_utc:
                        upcoming_7 += 1
                    if now_utc < t_dt <= next_30_utc:
                        upcoming_30 += 1

        return CalendarSummaryResponse(
            total_scheduled=total_scheduled,
            due_today=due_today,
            overdue=overdue,
            upcoming_7_days=upcoming_7,
            upcoming_30_days=upcoming_30,
            completed=completed,
            tasks_by_status=status_counts,
            tasks_by_priority=priority_counts,
        )

    def reschedule_task(
        self,
        db: Session,
        current_user: User,
        req: RescheduleTaskRequest,
    ) -> CalendarTaskItem:
        """Transactional task rescheduling, dates update, and duration recalculation."""
        task = db.query(Task).filter(Task.id == req.task_id, Task.is_deleted == False).first()
        if not task:
            raise ValueError("Task not found")

        # Multi-tenant authorization
        if task.user_id != current_user.id and task.assignee_id != current_user.id:
            # Check workspace ownership or project membership
            if task.workspace_id:
                wm = db.query(WorkspaceMember).filter(
                    WorkspaceMember.workspace_id == task.workspace_id,
                    WorkspaceMember.user_id == current_user.id
                ).first()
                if not wm:
                    raise ValueError("Unauthorized to reschedule this task")
            else:
                raise ValueError("Unauthorized to reschedule this task")

        tz = get_safe_timezone(req.timezone)
        if req.duration_minutes is not None:
            if req.duration_minutes <= 0:
                raise ValueError("Estimated duration minutes must be greater than 0")
            duration = req.duration_minutes
            task.estimated_duration_minutes = duration
            if task.scheduled_start and not req.new_start:
                task.scheduled_end = task.scheduled_start + timedelta(minutes=duration)
        else:
            duration = task.estimated_duration_minutes or 30

        if req.new_start:
            s_dt = req.new_start.astimezone(timezone.utc) if req.new_start.tzinfo else req.new_start.replace(tzinfo=timezone.utc)
            task.scheduled_start = s_dt
            task.scheduled_end = req.new_end.astimezone(timezone.utc) if req.new_end and req.new_end.tzinfo else (s_dt + timedelta(minutes=duration))
            task.estimated_duration_minutes = duration

        if req.new_due_date is not None:
            task.due_date = req.new_due_date
        if req.new_start_date is not None:
            task.start_date = req.new_start_date
        if req.is_all_day is not None:
            task.is_all_day = req.is_all_day

        db.commit()
        db.refresh(task)

        # Fetch project for label
        proj = db.query(Project).filter(Project.id == task.project_id).first() if task.project_id else None
        project_map = {proj.id: proj} if proj else {}

        now_utc = datetime.now(timezone.utc)
        return self._map_task_to_calendar_item(task, now_utc, tz, project_map)

    def detect_conflicts(self, db: Session, user_id: int) -> List[CalendarConflictItem]:
        """Detect overlapping scheduled tasks for the user."""
        tasks = (
            db.query(Task)
            .filter(
                Task.user_id == user_id,
                Task.scheduled_start.isnot(None),
                Task.is_deleted == False,
                func.lower(Task.status) != "completed",
            )
            .order_by(Task.scheduled_start)
            .all()
        )

        conflicts: List[CalendarConflictItem] = []
        for i in range(len(tasks)):
            t1 = tasks[i]
            dur1 = t1.estimated_duration_minutes or 30
            t1_start = t1.scheduled_start
            t1_end = t1.scheduled_end or (t1_start + timedelta(minutes=dur1))

            for j in range(i + 1, len(tasks)):
                t2 = tasks[j]
                dur2 = t2.estimated_duration_minutes or 30
                t2_start = t2.scheduled_start
                t2_end = t2.scheduled_end or (t2_start + timedelta(minutes=dur2))

                # If t2 starts after t1 ends, no more overlaps for t1
                if t2_start >= t1_end:
                    break
                # Overlap condition
                if t1_start < t2_end and t1_end > t2_start:
                    conflicts.append(
                        CalendarConflictItem(
                            task_id=str(t1.id),
                            task_title=t1.title,
                            conflict_type="OVERLAP",
                            conflicting_event_title=t2.title,
                            message=f"'{t1.title}' overlaps with '{t2.title}' between {t2_start.strftime('%H:%M')} and {t1_end.strftime('%H:%M')}."
                        )
                    )
        return conflicts

calendar_service = CalendarService()
