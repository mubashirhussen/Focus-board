from datetime import datetime, timezone
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.task import Task
from app.ai.schemas import (
    TaskBreakdownRequest,
    TaskBreakdownResponse,
    SubtaskProposal,
    WorkloadAnalysisResponse,
    ChatRequest,
    ChatResponse,
    ActionProposal,
    ApproveActionRequest,
)
from app.ai.prioritizer import prioritize_tasks
from app.ai.safety import check_prompt_safety, sanitize_user_input

class AIService:
    def __init__(self):
        self.provider = settings.AI_PROVIDER

    def break_down_task(self, req: TaskBreakdownRequest) -> TaskBreakdownResponse:
        """Break down a complex task into actionable subtasks with clear criteria."""
        title = sanitize_user_input(req.task_title)
        cat = req.category or "General"

        # Practical modular subtasks tailored by domain
        if "design" in (cat + title).lower():
            subtasks = [
                SubtaskProposal(
                    title="Audit existing UX wireframes and brand guidelines",
                    estimated_minutes=45,
                    order=1,
                    preparation="Review Figma design tokens and component specs.",
                    completion_criteria="Design inventory document created."
                ),
                SubtaskProposal(
                    title="Create high-fidelity layout and interactive component variants",
                    estimated_minutes=90,
                    order=2,
                    preparation="Ensure auto-layout and responsive constraints are set.",
                    completion_criteria="Figma mockups completed for desktop and mobile."
                ),
                SubtaskProposal(
                    title="Conduct contrast audit and export production assets",
                    estimated_minutes=30,
                    order=3,
                    preparation="Check WCAG 2.1 AA accessibility ratios.",
                    completion_criteria="SVG/PNG icons and design tokens packaged for handoff."
                ),
            ]
        elif "dev" in (cat + title).lower() or "code" in title.lower() or "api" in title.lower():
            subtasks = [
                SubtaskProposal(
                    title="Define API data contracts and database schema migration",
                    estimated_minutes=45,
                    order=1,
                    preparation="Review Pydantic request/response schemas.",
                    completion_criteria="Alembic migration scripts committed."
                ),
                SubtaskProposal(
                    title="Implement core business logic and service methods",
                    estimated_minutes=90,
                    order=2,
                    preparation="Set up dependency injection and unit test fixtures.",
                    completion_criteria="Service functions implemented and returning validated schemas."
                ),
                SubtaskProposal(
                    title="Write automated test suite and execute regression check",
                    estimated_minutes=45,
                    order=3,
                    preparation="Prepare mock fixtures and edge cases.",
                    completion_criteria="All unit and integration tests passing with 100% assertions."
                ),
            ]
        else:
            subtasks = [
                SubtaskProposal(
                    title="Clarify scope, deliverables, and success metrics",
                    estimated_minutes=30,
                    order=1,
                    preparation="Outline main constraints and timeline.",
                    completion_criteria="Scope bullet list validated."
                ),
                SubtaskProposal(
                    title="Execute core milestone work items",
                    estimated_minutes=90,
                    order=2,
                    preparation="Eliminate distractions and focus on critical path.",
                    completion_criteria="Primary draft or implementation finished."
                ),
                SubtaskProposal(
                    title="Review, refine, and verify quality against standards",
                    estimated_minutes=45,
                    order=3,
                    preparation="Run verification checklist.",
                    completion_criteria="Task ready for handoff or final completion."
                ),
            ]

        blockers = [
            "Unclear scope or changing specifications mid-flight.",
            "Missing external assets or dependency approval.",
            "Underestimating testing and edge-case handling."
        ]

        summary = (
            f"Broken down '{title}' into {len(subtasks)} manageable subtasks "
            f"totaling ~{sum(s.estimated_minutes for s in subtasks)} minutes."
        )

        return TaskBreakdownResponse(
            task_title=title,
            proposed_subtasks=subtasks,
            possible_blockers=blockers,
            summary=summary
        )

    def analyze_workload(self, tasks: List[Task]) -> WorkloadAnalysisResponse:
        """Analyze user incomplete tasks and evaluate schedule bottlenecks."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        incomplete = [t for t in tasks if (t.status or "").lower() != "completed"]

        overdue_count = 0
        due_today_count = 0
        high_p_count = 0
        est_minutes = 0

        for t in incomplete:
            p_lower = (t.priority or "medium").lower()
            if p_lower == "high":
                high_p_count += 1
                est_minutes += 90
            elif p_lower == "medium":
                est_minutes += 60
            else:
                est_minutes += 45

            if t.due_date:
                if t.due_date < today_str:
                    overdue_count += 1
                elif t.due_date == today_str:
                    due_today_count += 1

        total_hours = round(est_minutes / 60, 1)

        # Assessment
        if overdue_count > 2 or total_hours > 15:
            assessment = "Critical"
        elif overdue_count > 0 or total_hours > 8:
            assessment = "Heavy"
        else:
            assessment = "Balanced"

        bottlenecks = []
        if overdue_count > 0:
            bottlenecks.append(f"{overdue_count} task(s) past due require immediate deadline rescheduling.")
        if high_p_count > 4:
            bottlenecks.append(f"High concentration of critical tasks ({high_p_count}) creates priority competition.")
        if not bottlenecks:
            bottlenecks.append("No immediate bottlenecks identified. Workload is well distributed.")

        adjustments = [
            "Address overdue tasks first to relieve schedule tension.",
            "De-escalate low urgency tasks to Medium or Low priority.",
            "Protect 90-minute uninterrupted deep work blocks for primary tasks."
        ]

        return WorkloadAnalysisResponse(
            total_active_tasks=len(incomplete),
            overdue_count=overdue_count,
            due_today_count=due_today_count,
            high_priority_count=high_p_count,
            estimated_total_hours=total_hours,
            workload_assessment=assessment,
            bottlenecks=bottlenecks,
            suggested_adjustments=adjustments
        )

    def chat_with_assistant(self, req: ChatRequest, tasks: List[Task]) -> ChatResponse:
        """
        Interactive productivity chat assistant:
        - Evaluates user intent against real tasks.
        - Provides grounded answers (never hallucinates tasks not in DB).
        - Emits concrete ActionProposals for user approval when task modifications are indicated.
        """
        user_message = sanitize_user_input(req.message)

        if not check_prompt_safety(user_message):
            return ChatResponse(
                reply="I detected a safety conflict with your prompt. Please ask a productivity or task-related question.",
                task_references=[],
                proposed_actions=[]
            )

        msg_lower = user_message.lower()
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        incomplete_tasks = [t for t in tasks if (t.status or "").lower() != "completed"]

        task_refs: List[str] = []
        proposed_actions: List[ActionProposal] = []
        reply_lines: List[str] = []

        # 1. Intent: What should I work on today / Plan day
        if "what should i work on" in msg_lower or "today" in msg_lower or "plan" in msg_lower:
            ranked = prioritize_tasks(tasks)
            top_3 = ranked[:3]

            if not top_3:
                reply_lines.append("You have no pending tasks! Enjoy your day or create a new assignment to get started.")
            else:
                reply_lines.append("Here are your top recommended focus tasks based on deadline urgency and priority:")
                for idx, r in enumerate(top_3, 1):
                    task_refs.append(r.title)
                    reply_lines.append(f"{idx}. **{r.title}** ({r.urgency} urgency, {r.priority_score} pts) — {r.reason}")

                # Propose promoting the highest scored task if not yet high
                if top_3[0].suggested_priority != top_3[0].current_priority:
                    proposed_actions.append(ActionProposal(
                        proposal_id=f"prop-{uuid.uuid4().hex[:8]}",
                        action_type="update_priority",
                        task_id=top_3[0].task_id,
                        description=f"Promote '{top_3[0].title}' to {top_3[0].suggested_priority} priority",
                        payload={"priority": top_3[0].suggested_priority}
                    ))

        # 2. Intent: Overdue tasks
        elif "overdue" in msg_lower or "late" in msg_lower or "deadline" in msg_lower:
            overdue_tasks = [t for t in incomplete_tasks if t.due_date and t.due_date < today_str]
            if not overdue_tasks:
                reply_lines.append("Great news: None of your tasks are currently overdue! All deadlines are on track.")
            else:
                reply_lines.append(f"You have **{len(overdue_tasks)} overdue task(s)** requiring attention:")
                for t in overdue_tasks:
                    task_refs.append(t.title)
                    reply_lines.append(f"• **{t.title}** (Was due {t.due_date})")

                    # Propose rescheduling to today
                    proposed_actions.append(ActionProposal(
                        proposal_id=f"prop-{uuid.uuid4().hex[:8]}",
                        action_type="reschedule",
                        task_id=t.id,
                        description=f"Reschedule overdue '{t.title}' to today ({today_str})",
                        payload={"due_date": today_str}
                    ))

        # 3. Intent: Break down a task
        elif "break" in msg_lower or "subtask" in msg_lower or "steps" in msg_lower:
            target_task = incomplete_tasks[0] if incomplete_tasks else None
            # Find matching task in message if named
            for t in incomplete_tasks:
                if t.title.lower() in msg_lower:
                    target_task = t
                    break

            if target_task:
                task_refs.append(target_task.title)
                breakdown = self.break_down_task(TaskBreakdownRequest(
                    task_id=target_task.id,
                    task_title=target_task.title,
                    task_description=target_task.description or "",
                    category=target_task.category
                ))
                reply_lines.append(f"Here is a recommended 3-step breakdown for **{target_task.title}**:")
                for st in breakdown.proposed_subtasks:
                    reply_lines.append(f"{st.order}. **{st.title}** (~{st.estimated_minutes}m) — {st.completion_criteria}")
                    proposed_actions.append(ActionProposal(
                        proposal_id=f"prop-{uuid.uuid4().hex[:8]}",
                        action_type="create_subtask",
                        task_id=target_task.id,
                        description=f"Add subtask: {st.title}",
                        payload={
                            "title": f"[{target_task.title}] {st.title}",
                            "category": target_task.category,
                            "priority": target_task.priority,
                            "due_date": target_task.due_date
                        }
                    ))
            else:
                reply_lines.append("Which task would you like me to break down? Please mention its title.")

        # 4. Default productivity guidance
        else:
            analysis = self.analyze_workload(tasks)
            reply_lines.append(
                f"You currently have **{analysis.total_active_tasks} active task(s)** "
                f"({analysis.high_priority_count} high priority, {analysis.overdue_count} overdue). "
                f"Your workload is rated **{analysis.workload_assessment}** (~{analysis.estimated_total_hours} hours total). "
                f"You can ask me to plan your day, analyze deadlines, or break down any complex assignment."
            )

        return ChatResponse(
            reply="\n".join(reply_lines),
            task_references=list(set(task_refs)),
            proposed_actions=proposed_actions
        )

    def execute_approved_action(self, db: Session, user_id: int, req: ApproveActionRequest) -> Dict[str, Any]:
        """
        Execute an action explicitly approved by the user.
        Validates task ownership and enforces safe schema updates.
        """
        action_type = req.action_type
        task_id = req.task_id

        if action_type in ("update_priority", "reschedule") and task_id:
            task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
            if not task:
                raise ValueError("Task not found or access denied.")

            if action_type == "update_priority" and "priority" in req.payload:
                task.priority = req.payload["priority"]
                task.updated_at = datetime.now(timezone.utc)
                db.commit()
                return {"status": "success", "message": f"Updated task priority to {task.priority}."}

            if action_type == "reschedule" and "due_date" in req.payload:
                task.due_date = req.payload["due_date"]
                task.updated_at = datetime.now(timezone.utc)
                db.commit()
                return {"status": "success", "message": f"Rescheduled task due date to {task.due_date}."}

        elif action_type == "create_subtask":
            sub_title = req.payload.get("title", "").strip()
            if not sub_title:
                raise ValueError("Subtask title is required.")

            new_task = Task(
                id=f"task-{int(datetime.now(timezone.utc).timestamp()*1000)}-{uuid.uuid4().hex[:6]}",
                title=sub_title,
                description=req.payload.get("description", ""),
                category=req.payload.get("category", "Design"),
                status="Todo",
                priority=req.payload.get("priority", "Medium"),
                due_date=req.payload.get("due_date", ""),
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(new_task)
            db.commit()
            db.refresh(new_task)
            return {"status": "success", "message": f"Created subtask '{new_task.title}'.", "task_id": new_task.id}

        raise ValueError(f"Unsupported action type: {action_type}")

ai_service = AIService()
