"""Core Planning, Dependency Management, Critical Path Method (CPM),

Baselines, Budget, and What-If Simulation Service for FocusBoard Module B51.
"""

from datetime import datetime, timezone, timedelta
import json
import math
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.project import Project, ProjectMember
from app.models.task import Task, TaskDependency
from app.models.goals import GoalMilestone
from app.models.project_planning import (
    ProjectSchedule,
    ProjectBaseline,
    BaselineTaskSnapshot,
    BaselineMilestoneSnapshot,
    ProjectBudget,
    ProjectBudgetCategory,
    ProjectCostRecord,
    ProjectScheduleScenario,
    ScenarioTaskChange,
    ProjectScheduleForecast,
)
from app.models.time_tracking import TimeEntry


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime_safe(val: Any) -> Optional[datetime]:
    if not val:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, str):
        try:
            val = val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(val)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            try:
                dt = datetime.strptime(val[:10], "%Y-%m-%d")
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                return None
    return None


class ProjectPlanningService:
    @staticmethod
    def get_or_create_schedule(db: Session, project_id: int) -> ProjectSchedule:
        schedule = db.query(ProjectSchedule).filter(ProjectSchedule.project_id == project_id).first()
        if not schedule:
            project = db.query(Project).filter(Project.id == project_id).first()
            schedule = ProjectSchedule(
                project_id=project_id,
                organization_id=project.organization_id if project else None,
                planning_mode="CPM_DRIVEN",
                schedule_health="ON_TRACK",
                schedule_health_reasons_json="[]",
                planned_start_date=project.start_date if project else None,
                planned_end_date=project.due_date if project else None,
            )
            db.add(schedule)
            db.commit()
            db.refresh(schedule)
        return schedule

    @staticmethod
    def update_schedule_settings(db: Session, project_id: int, data: Dict[str, Any]) -> ProjectSchedule:
        schedule = ProjectPlanningService.get_or_create_schedule(db, project_id)
        if "planning_mode" in data:
            schedule.planning_mode = data["planning_mode"]
        if "working_days" in data:
            schedule.working_days_json = json.dumps(data["working_days"])
        if "working_hours_per_day" in data:
            schedule.working_hours_per_day = float(data["working_hours_per_day"])
        if "calendar_holidays" in data:
            schedule.calendar_holidays_json = json.dumps(data["calendar_holidays"])
        if "planned_start_date" in data:
            schedule.planned_start_date = parse_datetime_safe(data["planned_start_date"])
        if "planned_end_date" in data:
            schedule.planned_end_date = parse_datetime_safe(data["planned_end_date"])
        if "auto_recalculate" in data:
            schedule.auto_recalculate = bool(data["auto_recalculate"])

        schedule.updated_at = utc_now()
        db.commit()
        db.refresh(schedule)
        return schedule

    # =========================================================================
    # 1. TASK DEPENDENCIES & DAG CYCLE DETECTION
    # =========================================================================

    @staticmethod
    def validate_dependency_acyclic(db: Session, task_id: str, depends_on_task_id: str):
        """Ensure adding an edge depends_on_task_id -> task_id does not create a cycle."""
        if task_id == depends_on_task_id:
            raise ValueError("Self-dependencies are not allowed.")

        # Depth-First Search to check if task_id can reach depends_on_task_id
        visited = set()
        stack = [task_id]

        while stack:
            curr = stack.pop()
            if curr == depends_on_task_id:
                raise ValueError("Circular dependency detected. This dependency would create a cycle.")

            if curr not in visited:
                visited.add(curr)
                # Successors of curr: where task.depends_on_task_id == curr
                successors = (
                    db.query(TaskDependency.task_id)
                    .filter(TaskDependency.depends_on_task_id == curr)
                    .all()
                )
                for (s_id,) in successors:
                    if s_id not in visited:
                        stack.append(s_id)

    @staticmethod
    def create_task_dependency(
        db: Session,
        project_id: int,
        task_id: str,
        depends_on_task_id: str,
        dependency_type: str = "FINISH_TO_START",
        lag_duration: float = 0.0,
        lag_unit: str = "DAYS",
        created_by: Optional[int] = None,
    ) -> TaskDependency:
        task = db.query(Task).filter(Task.id == task_id).first()
        depends_on = db.query(Task).filter(Task.id == depends_on_task_id).first()

        if not task or not depends_on:
            raise ValueError("Both predecessor and successor tasks must exist.")

        # Cross-project check unless tasks are in the same project
        if task.project_id != project_id or depends_on.project_id != project_id:
            raise ValueError("Cross-project dependencies are prohibited in this planning workspace.")

        # Check for duplicate
        existing = (
            db.query(TaskDependency)
            .filter(
                TaskDependency.task_id == task_id,
                TaskDependency.depends_on_task_id == depends_on_task_id,
            )
            .first()
        )
        if existing:
            raise ValueError("Dependency relationship already exists between these tasks.")

        # Validate DAG
        ProjectPlanningService.validate_dependency_acyclic(db, task_id, depends_on_task_id)

        dep_id = f"dep_{int(datetime.now().timestamp()*1000)}_{task_id[:8]}_{depends_on_task_id[:8]}"
        dep = TaskDependency(
            id=dep_id,
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
            dependency_type=dependency_type,
            lag_duration=float(lag_duration),
            lag_unit=lag_unit.upper(),
            created_by=created_by,
            created_at=utc_now(),
        )
        db.add(dep)
        db.commit()
        db.refresh(dep)

        # Trigger CPM recalculation if enabled
        schedule = ProjectPlanningService.get_or_create_schedule(db, project_id)
        if schedule.auto_recalculate:
            ProjectPlanningService.calculate_critical_path(db, project_id)

        return dep

    @staticmethod
    def delete_task_dependency(db: Session, project_id: int, dependency_id: str):
        dep = db.query(TaskDependency).filter(TaskDependency.id == dependency_id).first()
        if not dep:
            raise ValueError("Dependency not found.")

        db.delete(dep)
        db.commit()

        schedule = ProjectPlanningService.get_or_create_schedule(db, project_id)
        if schedule.auto_recalculate:
            ProjectPlanningService.calculate_critical_path(db, project_id)

    @staticmethod
    def get_project_dependencies(db: Session, project_id: int) -> List[Dict[str, Any]]:
        task_ids = [t.id for t in db.query(Task.id).filter(Task.project_id == project_id).all()]
        if not task_ids:
            return []

        deps = (
            db.query(TaskDependency)
            .filter(TaskDependency.task_id.in_(task_ids))
            .all()
        )

        return [
            {
                "id": d.id,
                "task_id": d.task_id,
                "depends_on_task_id": d.depends_on_task_id,
                "dependency_type": d.dependency_type,
                "lag_duration": d.lag_duration,
                "lag_unit": d.lag_unit,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in deps
        ]

    # =========================================================================
    # 2. CRITICAL PATH METHOD (CPM) ENGINE
    # =========================================================================

    @staticmethod
    def calculate_critical_path(db: Session, project_id: int) -> Dict[str, Any]:
        """Calculates Earliest Start (ES), Earliest Finish (EF), Latest Start (LS),

        Latest Finish (LF), Total Float, Free Float, and Critical Path using CPM.
        """
        tasks = db.query(Task).filter(Task.project_id == project_id, Task.is_deleted == False).all()
        if not tasks:
            return {
                "critical_path": [],
                "critical_tasks_count": 0,
                "critical_path_duration_days": 0.0,
                "tasks_schedule": {},
            }

        task_map = {t.id: t for t in tasks}
        task_ids = set(task_map.keys())

        # Load dependencies
        deps = (
            db.query(TaskDependency)
            .filter(TaskDependency.task_id.in_(task_ids), TaskDependency.depends_on_task_id.in_(task_ids))
            .all()
        )

        # Adjacency structures
        predecessors: Dict[str, List[Tuple[str, str, float]]] = {t_id: [] for t_id in task_ids}
        successors: Dict[str, List[Tuple[str, str, float]]] = {t_id: [] for t_id in task_ids}

        for d in deps:
            # lag in days
            lag_days = d.lag_duration if d.lag_unit == "DAYS" else (d.lag_duration / 8.0)
            predecessors[d.task_id].append((d.depends_on_task_id, d.dependency_type, lag_days))
            successors[d.depends_on_task_id].append((d.task_id, d.dependency_type, lag_days))

        # Task duration in days (minimum 1 day)
        durations: Dict[str, float] = {}
        for t in tasks:
            d_days = 1.0
            if t.scheduled_start and t.scheduled_end:
                diff = (t.scheduled_end - t.scheduled_start).total_seconds() / 86400.0
                d_days = max(1.0, round(diff, 1))
            elif t.estimated_duration_minutes:
                d_days = max(0.5, round(t.estimated_duration_minutes / (8.0 * 60.0), 1))
            durations[t.id] = d_days

        # ---------------------------------------------------------------------
        # Forward Pass: Compute Earliest Start (ES) and Earliest Finish (EF)
        # ---------------------------------------------------------------------
        in_degree = {t_id: len(predecessors[t_id]) for t_id in task_ids}
        queue = [t_id for t_id in task_ids if in_degree[t_id] == 0]

        es: Dict[str, float] = {t_id: 0.0 for t_id in task_ids}
        ef: Dict[str, float] = {t_id: durations[t_id] for t_id in task_ids}

        # Topological traversal
        topo_order = []
        while queue:
            curr = queue.pop(0)
            topo_order.append(curr)

            # Recompute EF for curr
            ef[curr] = es[curr] + durations[curr]

            for succ_id, dep_type, lag in successors[curr]:
                if dep_type == "START_TO_START":
                    candidate_es = es[curr] + lag
                elif dep_type == "FINISH_TO_FINISH":
                    candidate_es = (ef[curr] + lag) - durations[succ_id]
                elif dep_type == "START_TO_FINISH":
                    candidate_es = (es[curr] + lag) - durations[succ_id]
                else:  # FINISH_TO_START
                    candidate_es = ef[curr] + lag

                es[succ_id] = max(es[succ_id], max(0.0, candidate_es))
                ef[succ_id] = es[succ_id] + durations[succ_id]

                in_degree[succ_id] -= 1
                if in_degree[succ_id] == 0:
                    queue.append(succ_id)

        # Handle any isolated cycles or nodes left
        for t_id in task_ids:
            if t_id not in topo_order:
                topo_order.append(t_id)
                ef[t_id] = es[t_id] + durations[t_id]

        project_finish_days = max([ef[t_id] for t_id in task_ids], default=0.0)

        # ---------------------------------------------------------------------
        # Backward Pass: Compute Latest Finish (LF) and Latest Start (LS)
        # ---------------------------------------------------------------------
        lf: Dict[str, float] = {t_id: project_finish_days for t_id in task_ids}
        ls: Dict[str, float] = {t_id: project_finish_days - durations[t_id] for t_id in task_ids}

        for curr in reversed(topo_order):
            if successors[curr]:
                min_lf = float("inf")
                for succ_id, dep_type, lag in successors[curr]:
                    if dep_type == "START_TO_START":
                        candidate_lf = ls[succ_id] - lag + durations[curr]
                    elif dep_type == "FINISH_TO_FINISH":
                        candidate_lf = lf[succ_id] - lag
                    elif dep_type == "START_TO_FINISH":
                        candidate_lf = lf[succ_id] - lag + durations[curr]
                    else:  # FINISH_TO_START
                        candidate_lf = ls[succ_id] - lag
                    min_lf = min(min_lf, candidate_lf)
                lf[curr] = max(durations[curr], min_lf)
            else:
                lf[curr] = project_finish_days

            ls[curr] = lf[curr] - durations[curr]

        # ---------------------------------------------------------------------
        # Floats & Critical Path
        # ---------------------------------------------------------------------
        total_float: Dict[str, float] = {}
        free_float: Dict[str, float] = {}
        critical_task_ids = []

        for t_id in task_ids:
            tf = round(ls[t_id] - es[t_id], 2)
            total_float[t_id] = max(0.0, tf)

            if successors[t_id]:
                min_succ_es = min(
                    [
                        es[succ_id] - (lag if dep_type == "FINISH_TO_START" else 0.0)
                        for succ_id, dep_type, lag in successors[t_id]
                    ],
                    default=ef[t_id],
                )
                ff = max(0.0, round(min_succ_es - ef[t_id], 2))
            else:
                ff = max(0.0, round(project_finish_days - ef[t_id], 2))
            free_float[t_id] = ff

            if abs(tf) < 0.1:  # Critical if total float ~ 0
                critical_task_ids.append(t_id)

        # Sort critical path by ES
        critical_path_tasks = sorted(critical_task_ids, key=lambda x: (es[x], -durations[x]))

        # Update ProjectSchedule record
        schedule = ProjectPlanningService.get_or_create_schedule(db, project_id)
        schedule.critical_path_duration_days = round(project_finish_days, 1)
        schedule.critical_tasks_count = len(critical_path_tasks)
        base_start = schedule.planned_start_date or utc_now()
        schedule.calculated_earliest_finish = base_start + timedelta(days=project_finish_days)
        schedule.updated_at = utc_now()
        db.commit()

        # Build task-level schedule map
        tasks_schedule = {}
        for t_id in task_ids:
            t = task_map[t_id]
            calc_start = base_start + timedelta(days=es[t_id])
            calc_end = base_start + timedelta(days=ef[t_id])
            tasks_schedule[t_id] = {
                "task_id": t_id,
                "title": t.title,
                "duration_days": durations[t_id],
                "es_days": round(es[t_id], 1),
                "ef_days": round(ef[t_id], 1),
                "ls_days": round(ls[t_id], 1),
                "lf_days": round(lf[t_id], 1),
                "total_float_days": total_float[t_id],
                "free_float_days": free_float[t_id],
                "is_critical": t_id in critical_task_ids,
                "calculated_start": calc_start.strftime("%Y-%m-%d"),
                "calculated_end": calc_end.strftime("%Y-%m-%d"),
                "status": t.status,
                "priority": t.priority,
                "progress_percent": t.progress_percent,
            }

        return {
            "project_id": project_id,
            "critical_path_duration_days": round(project_finish_days, 1),
            "critical_tasks_count": len(critical_path_tasks),
            "critical_path": [tasks_schedule[t_id] for t_id in critical_path_tasks],
            "tasks_schedule": tasks_schedule,
            "calculated_earliest_finish": schedule.calculated_earliest_finish.isoformat()
            if schedule.calculated_earliest_finish
            else None,
        }

    # =========================================================================
    # 3. PROJECT BASELINE MANAGEMENT
    # =========================================================================

    @staticmethod
    def create_project_baseline(
        db: Session,
        project_id: int,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> ProjectBaseline:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("Project not found.")

        # Determine version
        last_version = (
            db.query(func.max(ProjectBaseline.version))
            .filter(ProjectBaseline.project_id == project_id)
            .scalar()
            or 0
        )
        version = last_version + 1

        schedule = ProjectPlanningService.get_or_create_schedule(db, project_id)
        budget = db.query(ProjectBudget).filter(ProjectBudget.project_id == project_id).first()

        tasks = db.query(Task).filter(Task.project_id == project_id, Task.is_deleted == False).all()
        milestones = db.query(GoalMilestone).all()  # Related milestones

        total_effort = sum([float(t.estimated_duration_minutes or 30) / 60.0 for t in tasks])

        baseline = ProjectBaseline(
            project_id=project_id,
            name=name,
            description=description,
            version=version,
            is_active=True,
            is_archived=False,
            created_by=created_by,
            created_at=utc_now(),
            planned_start=schedule.planned_start_date or project.start_date,
            planned_end=schedule.planned_end_date or project.due_date,
            total_duration_days=schedule.critical_path_duration_days,
            total_estimated_effort_hours=round(total_effort, 1),
            total_budget=budget.total_budget if budget else 0.0,
            currency=budget.currency if budget else "USD",
            metadata_json=json.dumps({"tasks_count": len(tasks), "milestones_count": len(milestones)}),
        )
        db.add(baseline)
        db.commit()
        db.refresh(baseline)

        # Snapshot tasks
        for t in tasks:
            d_days = 1.0
            if t.scheduled_start and t.scheduled_end:
                d_days = max(1.0, (t.scheduled_end - t.scheduled_start).total_seconds() / 86400.0)
            t_snap = BaselineTaskSnapshot(
                baseline_id=baseline.id,
                task_id=t.id,
                title=t.title,
                start_date=t.start_date or (t.scheduled_start.strftime("%Y-%m-%d") if t.scheduled_start else None),
                due_date=t.due_date or (t.scheduled_end.strftime("%Y-%m-%d") if t.scheduled_end else None),
                duration_days=round(d_days, 1),
                progress_percent=t.progress_percent,
                estimated_effort_hours=round(float(t.estimated_duration_minutes or 30) / 60.0, 1),
                status=t.status,
                priority=t.priority,
                assignee_id=t.assignee_id,
            )
            db.add(t_snap)

        # Snapshot milestones
        for m in milestones:
            m_snap = BaselineMilestoneSnapshot(
                baseline_id=baseline.id,
                milestone_id=m.id,
                title=m.title,
                due_date=m.due_date.strftime("%Y-%m-%d") if m.due_date else None,
                status=m.status,
            )
            db.add(m_snap)

        schedule.active_baseline_id = baseline.id
        db.commit()
        db.refresh(baseline)
        return baseline

    @staticmethod
    def compare_baseline_with_current(db: Session, baseline_id: int) -> Dict[str, Any]:
        baseline = db.query(ProjectBaseline).filter(ProjectBaseline.id == baseline_id).first()
        if not baseline:
            raise ValueError("Baseline snapshot not found.")

        current_tasks = {
            t.id: t
            for t in db.query(Task).filter(Task.project_id == baseline.project_id, Task.is_deleted == False).all()
        }
        task_snapshots = {s.task_id: s for s in baseline.task_snapshots}

        task_variances = []
        delayed_tasks_count = 0
        advanced_tasks_count = 0

        for t_id, snap in task_snapshots.items():
            curr = current_tasks.get(t_id)
            if not curr:
                task_variances.append({
                    "task_id": t_id,
                    "title": snap.title,
                    "status_in_baseline": snap.status,
                    "current_status": "DELETED",
                    "schedule_variance_days": 0.0,
                    "is_delayed": False,
                })
                continue

            # Compare dates
            base_due = parse_datetime_safe(snap.due_date)
            curr_due = parse_datetime_safe(curr.due_date) or curr.scheduled_end

            variance_days = 0.0
            is_delayed = False
            is_advanced = False

            if base_due and curr_due:
                variance_days = round((curr_due - base_due).total_seconds() / 86400.0, 1)
                if variance_days > 0.5:
                    is_delayed = True
                    delayed_tasks_count += 1
                elif variance_days < -0.5:
                    is_advanced = True
                    advanced_tasks_count += 1

            task_variances.append({
                "task_id": t_id,
                "title": curr.title,
                "baseline_start": snap.start_date,
                "current_start": curr.start_date,
                "baseline_due": snap.due_date,
                "current_due": curr.due_date,
                "baseline_progress": snap.progress_percent,
                "current_progress": curr.progress_percent,
                "schedule_variance_days": variance_days,
                "is_delayed": is_delayed,
                "is_advanced": is_advanced,
                "status_in_baseline": snap.status,
                "current_status": curr.status,
            })

        # Project level variance
        schedule = ProjectPlanningService.get_or_create_schedule(db, baseline.project_id)
        current_finish = schedule.calculated_earliest_finish or schedule.planned_end_date
        base_finish = baseline.planned_end

        overall_variance_days = 0.0
        if current_finish and base_finish:
            overall_variance_days = round((current_finish - base_finish).total_seconds() / 86400.0, 1)

        budget = db.query(ProjectBudget).filter(ProjectBudget.project_id == baseline.project_id).first()
        budget_variance = (budget.actual_cost - baseline.total_budget) if budget else 0.0

        return {
            "baseline_id": baseline.id,
            "baseline_name": baseline.name,
            "version": baseline.version,
            "created_at": baseline.created_at.isoformat(),
            "overall_schedule_variance_days": overall_variance_days,
            "delayed_tasks_count": delayed_tasks_count,
            "advanced_tasks_count": advanced_tasks_count,
            "budget_variance": round(budget_variance, 2),
            "currency": baseline.currency,
            "task_variances": task_variances,
        }

    # =========================================================================
    # 4. PROJECT BUDGET MANAGEMENT
    # =========================================================================

    @staticmethod
    def get_or_create_budget(db: Session, project_id: int) -> ProjectBudget:
        budget = db.query(ProjectBudget).filter(ProjectBudget.project_id == project_id).first()
        if not budget:
            budget = ProjectBudget(
                project_id=project_id,
                currency="USD",
                total_budget=0.0,
                committed_cost=0.0,
                actual_cost=0.0,
                forecast_cost=0.0,
                is_approved=False,
            )
            db.add(budget)
            db.commit()
            db.refresh(budget)

            # Create standard default categories
            default_categories = [
                "Personnel",
                "Software",
                "Infrastructure",
                "Equipment",
                "Services",
                "External expenses",
            ]
            for cat_name in default_categories:
                cat = ProjectBudgetCategory(
                    budget_id=budget.id,
                    project_id=project_id,
                    category_name=cat_name,
                    budgeted_amount=0.0,
                    committed_amount=0.0,
                    actual_amount=0.0,
                    forecast_amount=0.0,
                )
                db.add(cat)
            db.commit()
            db.refresh(budget)
        return budget

    @staticmethod
    def update_budget(
        db: Session,
        project_id: int,
        total_budget: float,
        currency: str = "USD",
        notes: Optional[str] = None,
        is_approved: Optional[bool] = None,
        user_id: Optional[int] = None,
    ) -> ProjectBudget:
        budget = ProjectPlanningService.get_or_create_budget(db, project_id)
        budget.total_budget = max(0.0, float(total_budget))
        budget.currency = currency.upper()
        if notes is not None:
            budget.notes = notes
        if is_approved is not None:
            budget.is_approved = is_approved
            if is_approved:
                budget.approved_by = user_id
                budget.approved_at = utc_now()

        budget.updated_at = utc_now()
        db.commit()
        db.refresh(budget)
        return budget

    @staticmethod
    def add_cost_record(
        db: Session,
        project_id: int,
        description: str,
        amount: float,
        category_id: Optional[int] = None,
        record_type: str = "ACTUAL",
        currency: str = "USD",
        user_id: Optional[int] = None,
    ) -> ProjectCostRecord:
        budget = ProjectPlanningService.get_or_create_budget(db, project_id)
        cost_record = ProjectCostRecord(
            project_id=project_id,
            budget_id=budget.id,
            category_id=category_id,
            description=description,
            amount=max(0.0, float(amount)),
            currency=currency.upper(),
            record_type=record_type.upper(),
            date_incurred=utc_now(),
            created_by=user_id,
            created_at=utc_now(),
        )
        db.add(cost_record)

        # Update category
        if category_id:
            cat = db.query(ProjectBudgetCategory).filter(ProjectBudgetCategory.id == category_id).first()
            if cat:
                if record_type.upper() == "ACTUAL":
                    cat.actual_amount += float(amount)
                elif record_type.upper() == "COMMITTED":
                    cat.committed_amount += float(amount)

        # Update budget totals
        if record_type.upper() == "ACTUAL":
            budget.actual_cost += float(amount)
        elif record_type.upper() == "COMMITTED":
            budget.committed_cost += float(amount)

        budget.updated_at = utc_now()
        db.commit()
        db.refresh(cost_record)
        return cost_record

    @staticmethod
    def get_budget_summary(db: Session, project_id: int) -> Dict[str, Any]:
        budget = ProjectPlanningService.get_or_create_budget(db, project_id)
        categories = db.query(ProjectBudgetCategory).filter(ProjectBudgetCategory.budget_id == budget.id).all()
        costs = (
            db.query(ProjectCostRecord)
            .filter(ProjectCostRecord.budget_id == budget.id)
            .order_by(ProjectCostRecord.date_incurred.desc())
            .limit(50)
            .all()
        )

        remaining_budget = max(0.0, budget.total_budget - budget.actual_cost)
        # Budget Variance = Actual Cost - Approved Budget (positive means over budget)
        budget_variance = budget.actual_cost - budget.total_budget

        return {
            "budget_id": budget.id,
            "project_id": project_id,
            "currency": budget.currency,
            "total_budget": round(budget.total_budget, 2),
            "committed_cost": round(budget.committed_cost, 2),
            "actual_cost": round(budget.actual_cost, 2),
            "forecast_cost": round(budget.actual_cost + budget.committed_cost, 2),
            "remaining_budget": round(remaining_budget, 2),
            "budget_variance": round(budget_variance, 2),
            "is_over_budget": budget.actual_cost > budget.total_budget if budget.total_budget > 0 else False,
            "is_approved": budget.is_approved,
            "notes": budget.notes,
            "categories": [
                {
                    "id": c.id,
                    "category_name": c.category_name,
                    "budgeted_amount": round(c.budgeted_amount, 2),
                    "committed_amount": round(c.committed_amount, 2),
                    "actual_amount": round(c.actual_amount, 2),
                    "variance": round(c.actual_amount - c.budgeted_amount, 2),
                }
                for c in categories
            ],
            "recent_costs": [
                {
                    "id": cr.id,
                    "description": cr.description,
                    "amount": round(cr.amount, 2),
                    "currency": cr.currency,
                    "record_type": cr.record_type,
                    "date_incurred": cr.date_incurred.strftime("%Y-%m-%d"),
                }
                for cr in costs
            ],
        }

    # =========================================================================
    # 5. SCHEDULE FORECASTING & HEALTH EVALUATION
    # =========================================================================

    @staticmethod
    def generate_schedule_forecast(db: Session, project_id: int) -> Dict[str, Any]:
        schedule = ProjectPlanningService.get_or_create_schedule(db, project_id)
        cpm_result = ProjectPlanningService.calculate_critical_path(db, project_id)

        project = db.query(Project).filter(Project.id == project_id).first()
        tasks = db.query(Task).filter(Task.project_id == project_id, Task.is_deleted == False).all()

        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status in ("Completed", "Done")])
        delayed_tasks = 0

        now = utc_now()
        for t in tasks:
            due = parse_datetime_safe(t.due_date) or t.scheduled_end
            if due and due < now and t.status not in ("Completed", "Done"):
                delayed_tasks += 1

        # Calculate forecast completion date
        planned_end = schedule.planned_end_date or (project.due_date if project else None)
        calculated_finish = schedule.calculated_earliest_finish

        forecast_date = calculated_finish or (now + timedelta(days=cpm_result["critical_path_duration_days"]))

        variance_days = 0.0
        if planned_end and forecast_date:
            variance_days = round((forecast_date - planned_end).total_seconds() / 86400.0, 1)

        # Health Classifier
        health_reasons = []
        if total_tasks == 0:
            health_status = "INSUFFICIENT_DATA"
            health_reasons.append("Project currently contains no active tasks.")
        elif variance_days > 14 or delayed_tasks > (total_tasks * 0.4):
            health_status = "CRITICAL"
            health_reasons.append(f"Significant schedule delay of {variance_days} days detected.")
            health_reasons.append(f"{delayed_tasks} of {total_tasks} tasks are overdue.")
        elif variance_days > 5 or delayed_tasks > (total_tasks * 0.2):
            health_status = "DELAYED"
            health_reasons.append(f"Forecast completion exceeds planned delivery by {variance_days} days.")
        elif variance_days > 0 or cpm_result["critical_tasks_count"] > (total_tasks * 0.5):
            health_status = "AT_RISK"
            health_reasons.append(f"Critical path represents {cpm_result['critical_tasks_count']} critical tasks with zero float.")
        else:
            health_status = "ON_TRACK"
            health_reasons.append("Tasks and critical path duration align with planned project delivery dates.")

        schedule.schedule_health = health_status
        schedule.schedule_health_reasons_json = json.dumps(health_reasons)
        schedule.forecast_completion_date = forecast_date
        schedule.schedule_variance_days = variance_days
        db.commit()

        # Persist forecast record
        forecast_rec = ProjectScheduleForecast(
            project_id=project_id,
            planned_completion_date=planned_end,
            forecast_completion_date=forecast_date,
            schedule_variance_days=variance_days,
            critical_path_duration_days=cpm_result["critical_path_duration_days"],
            health_status=health_status,
            confidence_score=0.88 if total_tasks >= 5 else 0.65,
            calculation_factors_json=json.dumps({
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "delayed_tasks": delayed_tasks,
                "critical_tasks_count": cpm_result["critical_tasks_count"],
            }),
            calculated_at=now,
        )
        db.add(forecast_rec)
        db.commit()

        return {
            "project_id": project_id,
            "health_status": health_status,
            "health_reasons": health_reasons,
            "planned_completion_date": planned_end.strftime("%Y-%m-%d") if planned_end else None,
            "forecast_completion_date": forecast_date.strftime("%Y-%m-%d") if forecast_date else None,
            "schedule_variance_days": variance_days,
            "critical_path_duration_days": cpm_result["critical_path_duration_days"],
            "critical_tasks_count": cpm_result["critical_tasks_count"],
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "delayed_tasks": delayed_tasks,
            "confidence_score": forecast_rec.confidence_score,
        }

    # =========================================================================
    # 6. WHAT-IF SCHEDULING SIMULATIONS
    # =========================================================================

    @staticmethod
    def create_scenario(
        db: Session,
        project_id: int,
        name: str,
        description: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> ProjectScheduleScenario:
        scenario = ProjectScheduleScenario(
            project_id=project_id,
            name=name,
            description=description,
            status="DRAFT",
            created_by=user_id,
            created_at=utc_now(),
        )
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        return scenario

    @staticmethod
    def add_scenario_task_change(
        db: Session,
        scenario_id: int,
        task_id: str,
        proposed_start_date: Optional[str] = None,
        proposed_due_date: Optional[str] = None,
        proposed_duration_days: Optional[float] = None,
        proposed_priority: Optional[str] = None,
        proposed_assignee_id: Optional[int] = None,
    ) -> ScenarioTaskChange:
        change = (
            db.query(ScenarioTaskChange)
            .filter(ScenarioTaskChange.scenario_id == scenario_id, ScenarioTaskChange.task_id == task_id)
            .first()
        )
        if not change:
            change = ScenarioTaskChange(
                scenario_id=scenario_id,
                task_id=task_id,
            )
            db.add(change)

        if proposed_start_date is not None:
            change.proposed_start_date = proposed_start_date
        if proposed_due_date is not None:
            change.proposed_due_date = proposed_due_date
        if proposed_duration_days is not None:
            change.proposed_duration_days = float(proposed_duration_days)
        if proposed_priority is not None:
            change.proposed_priority = proposed_priority
        if proposed_assignee_id is not None:
            change.proposed_assignee_id = proposed_assignee_id

        db.commit()
        db.refresh(change)
        return change

    @staticmethod
    def simulate_scenario(db: Session, scenario_id: int) -> Dict[str, Any]:
        """Runs CPM simulation in memory using proposed scenario changes without

        mutating the real production database.
        """
        scenario = db.query(ProjectScheduleScenario).filter(ProjectScheduleScenario.id == scenario_id).first()
        if not scenario:
            raise ValueError("Scenario not found.")

        project_id = scenario.project_id
        tasks = db.query(Task).filter(Task.project_id == project_id, Task.is_deleted == False).all()
        changes = {c.task_id: c for c in scenario.task_changes}

        # Apply simulation changes in virtual task mapping
        sim_durations = {}
        for t in tasks:
            chg = changes.get(t.id)
            if chg and chg.proposed_duration_days is not None:
                sim_durations[t.id] = max(0.5, float(chg.proposed_duration_days))
            elif t.scheduled_start and t.scheduled_end:
                sim_durations[t.id] = max(1.0, round((t.scheduled_end - t.scheduled_start).total_seconds() / 86400.0, 1))
            else:
                sim_durations[t.id] = max(0.5, round(float(t.estimated_duration_minutes or 30) / (8.0 * 60.0), 1))

        # Run virtual CPM calculation
        task_ids = set([t.id for t in tasks])
        deps = (
            db.query(TaskDependency)
            .filter(TaskDependency.task_id.in_(task_ids), TaskDependency.depends_on_task_id.in_(task_ids))
            .all()
        )

        predecessors: Dict[str, List[Tuple[str, str, float]]] = {t_id: [] for t_id in task_ids}
        successors: Dict[str, List[Tuple[str, str, float]]] = {t_id: [] for t_id in task_ids}
        for d in deps:
            lag = d.lag_duration if d.lag_unit == "DAYS" else (d.lag_duration / 8.0)
            predecessors[d.task_id].append((d.depends_on_task_id, d.dependency_type, lag))
            successors[d.depends_on_task_id].append((d.task_id, d.dependency_type, lag))

        in_degree = {t_id: len(predecessors[t_id]) for t_id in task_ids}
        queue = [t_id for t_id in task_ids if in_degree[t_id] == 0]

        es: Dict[str, float] = {t_id: 0.0 for t_id in task_ids}
        ef: Dict[str, float] = {t_id: sim_durations[t_id] for t_id in task_ids}

        topo = []
        while queue:
            curr = queue.pop(0)
            topo.append(curr)
            ef[curr] = es[curr] + sim_durations[curr]
            for succ_id, dep_type, lag in successors[curr]:
                c_es = ef[curr] + lag
                es[succ_id] = max(es[succ_id], max(0.0, c_es))
                ef[succ_id] = es[succ_id] + sim_durations[succ_id]
                in_degree[succ_id] -= 1
                if in_degree[succ_id] == 0:
                    queue.append(succ_id)

        sim_project_finish = max([ef[t_id] for t_id in task_ids], default=0.0)

        # Baseline comparison
        schedule = ProjectPlanningService.get_or_create_schedule(db, project_id)
        current_cpm = schedule.critical_path_duration_days
        delta_days = round(sim_project_finish - current_cpm, 1)

        outcomes = {
            "simulated_critical_path_duration_days": round(sim_project_finish, 1),
            "baseline_critical_path_duration_days": current_cpm,
            "variance_from_current_days": delta_days,
            "tasks_modified_count": len(changes),
            "is_accelerated": delta_days < 0,
            "is_delayed": delta_days > 0,
        }

        scenario.status = "SIMULATED"
        scenario.outcomes_json = json.dumps(outcomes)
        db.commit()
        db.refresh(scenario)

        return {
            "scenario_id": scenario.id,
            "name": scenario.name,
            "status": scenario.status,
            "outcomes": outcomes,
        }

    @staticmethod
    def apply_scenario(db: Session, scenario_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Atomically applies scenario changes to the real tasks table after explicit confirmation."""
        scenario = db.query(ProjectScheduleScenario).filter(ProjectScheduleScenario.id == scenario_id).first()
        if not scenario:
            raise ValueError("Scenario not found.")

        changes = scenario.task_changes
        applied_count = 0

        for chg in changes:
            task = db.query(Task).filter(Task.id == chg.task_id).first()
            if task:
                if chg.proposed_start_date:
                    task.start_date = chg.proposed_start_date
                if chg.proposed_due_date:
                    task.due_date = chg.proposed_due_date
                if chg.proposed_duration_days is not None:
                    task.estimated_duration_minutes = int(chg.proposed_duration_days * 8 * 60)
                if chg.proposed_priority:
                    task.priority = chg.proposed_priority
                if chg.proposed_assignee_id is not None:
                    task.assignee_id = chg.proposed_assignee_id
                applied_count += 1

        scenario.status = "APPLIED"
        scenario.applied_at = utc_now()
        db.commit()

        # Recalculate CPM for real schedule
        ProjectPlanningService.calculate_critical_path(db, scenario.project_id)
        ProjectPlanningService.generate_schedule_forecast(db, scenario.project_id)

        return {
            "scenario_id": scenario.id,
            "status": "APPLIED",
            "tasks_applied_count": applied_count,
            "applied_at": scenario.applied_at.isoformat(),
        }

    # =========================================================================
    # 7. HIGH-LEVEL PLANNING WORKSPACE METRICS
    # =========================================================================

    @staticmethod
    def get_planning_workspace_overview(db: Session, project_id: int) -> Dict[str, Any]:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("Project not found.")

        schedule = ProjectPlanningService.get_or_create_schedule(db, project_id)
        cpm = ProjectPlanningService.calculate_critical_path(db, project_id)
        budget = ProjectPlanningService.get_budget_summary(db, project_id)
        forecast = ProjectPlanningService.generate_schedule_forecast(db, project_id)

        tasks = db.query(Task).filter(Task.project_id == project_id, Task.is_deleted == False).all()
        milestones = db.query(GoalMilestone).all()
        baselines = (
            db.query(ProjectBaseline)
            .filter(ProjectBaseline.project_id == project_id, ProjectBaseline.is_archived == False)
            .order_by(ProjectBaseline.version.desc())
            .all()
        )
        scenarios = (
            db.query(ProjectScheduleScenario)
            .filter(ProjectScheduleScenario.project_id == project_id)
            .order_by(ProjectScheduleScenario.created_at.desc())
            .all()
        )

        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "health": project.health,
                "priority": project.priority,
                "start_date": project.start_date.strftime("%Y-%m-%d") if project.start_date else None,
                "due_date": project.due_date.strftime("%Y-%m-%d") if project.due_date else None,
            },
            "schedule": {
                "planning_mode": schedule.planning_mode,
                "schedule_health": schedule.schedule_health,
                "schedule_health_reasons": schedule.schedule_health_reasons,
                "critical_path_duration_days": schedule.critical_path_duration_days,
                "critical_tasks_count": schedule.critical_tasks_count,
                "calculated_earliest_finish": schedule.calculated_earliest_finish.strftime("%Y-%m-%d")
                if schedule.calculated_earliest_finish
                else None,
                "forecast_completion_date": schedule.forecast_completion_date.strftime("%Y-%m-%d")
                if schedule.forecast_completion_date
                else None,
                "schedule_variance_days": schedule.schedule_variance_days,
            },
            "tasks_summary": {
                "total": len(tasks),
                "completed": len([t for t in tasks if t.status in ("Completed", "Done")]),
                "in_progress": len([t for t in tasks if t.status in ("In Progress", "Review")]),
                "todo": len([t for t in tasks if t.status in ("Todo", "Blocked")]),
            },
            "critical_path": cpm["critical_path"],
            "budget": budget,
            "forecast": forecast,
            "milestones_count": len(milestones),
            "baselines_count": len(baselines),
            "scenarios_count": len(scenarios),
        }
