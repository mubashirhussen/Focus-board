from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.task import Task
from app.api.dependencies import get_current_user
from app.schemas.ai import (
    TaskPriorityRecommendation,
    DailyPlanRequest,
    DailyPlanResponse,
    TaskBreakdownRequest,
    TaskBreakdownResponse,
    WorkloadAnalysisResponse,
    ChatRequest,
    ChatResponse,
    ApproveActionRequest,
    AIConversationCreate,
    AIConversationUpdate,
    AIConversationResponse,
    AIConversationDetailResponse,
    AIMessageResponse,
    TaskDescriptionRequest,
    TaskDescriptionResponse,
    TaskDecomposeRequest,
    TaskDecomposeResponse,
    TaskPlanRequest,
    TaskPlanResponse,
    TaskCreateAssistRequest,
    TaskCreateAssistResponse,
    ProjectSummaryResponse,
    ProjectPlanRequest,
    ProjectPlanResponse,
    ProjectRiskResponse,
    AnalyticsInterpretRequest,
    AnalyticsInterpretResponse,
    AIUsageSummaryResponse,
)
from app.ai.prioritizer import prioritize_tasks
from app.ai.planner import generate_daily_plan
from app.ai.service import ai_service

router = APIRouter(prefix="/ai", tags=["AI Productivity Assistant & Intelligence"])

# -------------------------------------------------------------
# Existing / Backward-Compatible Endpoints
# -------------------------------------------------------------

@router.get("/priorities", response_model=List[TaskPriorityRecommendation])
def get_priorities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate deterministic priority recommendations for the user's active tasks.
    Evaluates deadline urgency, base priority, and execution momentum.
    """
    tasks = db.query(Task).filter(Task.user_id == current_user.id, Task.is_deleted == False).all()
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
    tasks = db.query(Task).filter(Task.user_id == current_user.id, Task.is_deleted == False).all()
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
    tasks = db.query(Task).filter(Task.user_id == current_user.id, Task.is_deleted == False).all()
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
    return ai_service.chat_with_assistant(db=db, current_user=current_user, req=chat_req)

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

# -------------------------------------------------------------
# Conversation Management Endpoints (Phase B13)
# -------------------------------------------------------------

@router.post("/conversations", response_model=AIConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conv_in: AIConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a persistent AI assistant conversation session."""
    conv = ai_service.create_conversation(db, current_user, conv_in)
    return conv

@router.get("/conversations", response_model=List[AIConversationResponse])
def list_conversations(
    workspace_id: Optional[int] = Query(None),
    is_archived: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all conversations accessible to the authenticated user."""
    convs = ai_service.list_conversations(
        db, current_user, workspace_id=workspace_id, is_archived=is_archived, limit=limit, skip=skip
    )
    result = []
    for c in convs:
        resp = AIConversationResponse.model_validate(c)
        resp.message_count = len(c.messages)
        result.append(resp)
    return result

@router.get("/conversations/{conversation_id}", response_model=AIConversationDetailResponse)
def get_conversation_details(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full conversation details along with its chronological message thread."""
    conv = ai_service.get_conversation(db, current_user, conversation_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages_data = [
        AIMessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            model=m.model,
            provider=m.provider,
            tokens_input=m.tokens_input,
            tokens_output=m.tokens_output,
            total_tokens=m.total_tokens,
            task_references=[],
            proposed_actions=[],
            created_at=m.created_at,
        )
        for m in conv.messages
    ]

    resp = AIConversationDetailResponse.model_validate(conv)
    resp.messages = messages_data
    resp.message_count = len(messages_data)
    return resp

@router.patch("/conversations/{conversation_id}", response_model=AIConversationResponse)
def update_conversation(
    conversation_id: str,
    data: AIConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update conversation title or archive state."""
    try:
        conv = ai_service.update_conversation(db, current_user, conversation_id, data)
        return conv
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete conversation and all associated message history."""
    deleted = ai_service.delete_conversation(db, current_user, conversation_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return {"status": "success", "message": "Conversation deleted successfully."}

@router.get("/conversations/{conversation_id}/messages", response_model=List[AIMessageResponse])
def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve paginated messages for a specific conversation."""
    try:
        messages = ai_service.get_conversation_messages(db, current_user, conversation_id, limit=limit, skip=skip)
        return [
            AIMessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                model=m.model,
                provider=m.provider,
                tokens_input=m.tokens_input,
                tokens_output=m.tokens_output,
                total_tokens=m.total_tokens,
                task_references=[],
                proposed_actions=[],
                created_at=m.created_at,
            )
            for m in messages
        ]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# -------------------------------------------------------------
# Task AI Endpoints (Phase B13)
# -------------------------------------------------------------

@router.post("/tasks/generate-description", response_model=TaskDescriptionResponse)
def generate_task_description(
    req: TaskDescriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate structured task description and acceptance criteria from title & context."""
    return ai_service.generate_task_description(db, current_user, req)

@router.post("/tasks/decompose", response_model=TaskDecomposeResponse)
def decompose_task(
    req: TaskDecomposeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Break down a complex task into actionable subtasks with time estimates and acceptance criteria."""
    return ai_service.decompose_task(db, current_user, req)

@router.post("/tasks/plan", response_model=TaskPlanResponse)
def plan_task(
    req: TaskPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a structured action plan with ordered steps and focus recommendations."""
    return ai_service.plan_task(db, current_user, req)

@router.post("/tasks/create-assist", response_model=TaskCreateAssistResponse)
def create_task_assist(
    req: TaskCreateAssistRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Convert conversational user instructions into a validated FocusBoard task creation payload."""
    return ai_service.create_task_assist(db, current_user, req)

# -------------------------------------------------------------
# Project AI Endpoints (Phase B13)
# -------------------------------------------------------------

@router.get("/projects/{project_id}/summary", response_model=ProjectSummaryResponse)
def get_project_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate evidence-grounded project executive summary based on real task metrics."""
    try:
        return ai_service.get_project_summary(db, current_user, project_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/projects/plan", response_model=ProjectPlanResponse)
def plan_project(
    req: ProjectPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate structured project roadmap with phases, timeline, and risk factors."""
    return ai_service.generate_project_plan(db, current_user, req)

@router.get("/projects/{project_id}/risk-analysis", response_model=ProjectRiskResponse)
def analyze_project_risk(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluate project risks, schedule adherence, and bottleneck mitigation strategies."""
    try:
        return ai_service.analyze_project_risk(db, current_user, project_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# -------------------------------------------------------------
# Analytics & Usage Intelligence (Phase B13)
# -------------------------------------------------------------

@router.post("/analytics/interpret", response_model=AnalyticsInterpretResponse)
def interpret_analytics(
    req: AnalyticsInterpretRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Provide natural-language interpretation of analytics KPIs and workload velocity."""
    return ai_service.interpret_analytics(db, current_user, req)

@router.get("/usage", response_model=AIUsageSummaryResponse)
def get_ai_usage(
    workspace_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve aggregated AI token consumption, request counts, and cost tracking."""
    return ai_service.get_usage_summary(db, current_user, workspace_id=workspace_id, days=days)
