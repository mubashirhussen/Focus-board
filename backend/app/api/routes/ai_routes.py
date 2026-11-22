from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.task import Task
from app.api.dependencies import get_current_user
from app.ai.schemas import (
    TaskPriorityRecommendation,
    DailyPlanRequest,
    DailyPlanResponse,
    TaskBreakdownRequest,
    TaskBreakdownResponse,
    WorkloadAnalysisResponse,
    ChatRequest,
    ChatResponse,
    ApproveActionRequest,
)
from app.ai.prioritizer import prioritize_tasks
from app.ai.planner import generate_daily_plan
from app.ai.service import ai_service

router = APIRouter(prefix="/ai", tags=["AI Productivity Assistant"])

@router.get("/priorities", response_model=List[TaskPriorityRecommendation])
def get_priorities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate deterministic priority recommendations for the user's active tasks.
    Evaluates deadline urgency, base priority, and execution momentum.
    """
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    return prioritize_tasks(tasks)

@router.post("/daily-plan", response_model=DailyPlanResponse)
def create_daily_plan(
    plan_req: DailyPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate an intelligent daily work schedule matching the user's available hours.
    Allocates conservative time estimates and inter-task rest transitions.
    """
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    return generate_daily_plan(tasks, plan_req)

@router.post("/task-breakdown", response_model=TaskBreakdownResponse)
def breakdown_task(
    breakdown_req: TaskBreakdownRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Break down a complex assignment into 3 practical, actionable subtasks
    with clear completion criteria and blocker warnings.
    """
    return ai_service.break_down_task(breakdown_req)

@router.get("/workload-analysis", response_model=WorkloadAnalysisResponse)
def analyze_workload(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze user workload, identifying schedule bottlenecks, overdue stress points,
    and estimated total effort based on actual task records.
    """
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    return ai_service.analyze_workload(tasks)

@router.post("/chat", response_model=ChatResponse)
def chat_assistant(
    chat_req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Contextual productivity assistant answering questions grounded in the user's
    actual tasks. Emits ActionProposals for user review and explicit approval.
    """
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    return ai_service.chat_with_assistant(chat_req, tasks)

@router.post("/approve-action")
def approve_action(
    approval_req: ApproveActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute an AI-proposed action explicitly accepted by the user.
    Enforces user ownership and validates all schema modifications.
    """
    try:
        result = ai_service.execute_approved_action(db, current_user.id, approval_req)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
