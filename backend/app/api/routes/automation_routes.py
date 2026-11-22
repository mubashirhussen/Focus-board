from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.automation import (
    AutomationExecution,
    AutomationExecutionLog,
    AutomationApproval,
    AutomationWorkflowVersion,
)
from app.schemas.automation import (
    AutomationWorkflowCreate,
    AutomationWorkflowUpdate,
    AutomationWorkflowResponse,
    AutomationWorkflowVersionResponse,
    AutomationExecutionResponse,
    AutomationExecutionLogResponse,
    AutomationApprovalResponse,
    ApprovalDecisionRequest,
    TriggerWorkflowRequest,
    AIWorkflowGenerateRequest,
    AIWorkflowGenerateResponse,
    AutomationDashboardOverviewResponse,
)
from app.services import automation_engine_service

router = APIRouter(prefix="/automation", tags=["FocusBoard Automation Intelligence"])

@router.get("/overview", response_model=AutomationDashboardOverviewResponse)
def get_automation_overview(
    workspace_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full dashboard overview with metrics, active workflows, recent executions, and pending approvals."""
    return automation_engine_service.get_automation_overview(db, workspace_id=workspace_id)

# --- Workflows CRUD ---
@router.get("/workflows", response_model=List[AutomationWorkflowResponse])
def list_workflows(
    workspace_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    is_template: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List workflows filtered by workspace, status, or template flag."""
    return automation_engine_service.get_workflows(
        db,
        workspace_id=workspace_id,
        status=status,
        is_template=is_template,
    )

@router.get("/workflows/{workflow_id}", response_model=AutomationWorkflowResponse)
def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single workflow details."""
    wf = automation_engine_service.get_workflow_by_id(db, workflow_id)
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return wf

@router.post("/workflows", response_model=AutomationWorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    payload: AutomationWorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new automation workflow and initialize its version 1.0."""
    return automation_engine_service.create_workflow(db, payload, owner_id=current_user.id)

@router.patch("/workflows/{workflow_id}", response_model=AutomationWorkflowResponse)
def update_workflow(
    workflow_id: str,
    payload: AutomationWorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update workflow configuration, incrementing version if nodes changed."""
    updated = automation_engine_service.update_workflow(db, workflow_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return updated

@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a workflow."""
    success = automation_engine_service.delete_workflow(db, workflow_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return None

@router.get("/workflows/{workflow_id}/versions", response_model=List[AutomationWorkflowVersionResponse])
def get_workflow_versions(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get historical version records of the workflow."""
    return db.query(AutomationWorkflowVersion).filter(
        AutomationWorkflowVersion.workflow_id == workflow_id
    ).order_by(desc(AutomationWorkflowVersion.created_at)).all()

# --- Execution Engine ---
@router.post("/workflows/{workflow_id}/trigger", response_model=AutomationExecutionResponse)
def trigger_workflow(
    workflow_id: str,
    payload: TriggerWorkflowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger manual or dry-run execution of a workflow."""
    try:
        execution = automation_engine_service.trigger_workflow_execution(
            db=db,
            workflow_id=workflow_id,
            trigger_event=payload.trigger_event,
            payload=payload.payload,
            actor_id=current_user.id,
            dry_run=payload.dry_run,
        )
        return execution
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/executions", response_model=List[AutomationExecutionResponse])
def list_executions(
    workflow_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List execution runs with optional filters."""
    query = db.query(AutomationExecution)
    if workflow_id:
        query = query.filter(AutomationExecution.workflow_id == workflow_id)
    if status:
        query = query.filter(AutomationExecution.status == status)
    return query.order_by(desc(AutomationExecution.started_at)).offset(offset).limit(limit).all()

@router.get("/executions/{execution_id}", response_model=AutomationExecutionResponse)
def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single execution status."""
    exec_run = db.query(AutomationExecution).filter(AutomationExecution.id == execution_id).first()
    if not exec_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return exec_run

@router.get("/executions/{execution_id}/logs", response_model=List[AutomationExecutionLogResponse])
def get_execution_logs(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get node-by-node execution logs."""
    return db.query(AutomationExecutionLog).filter(
        AutomationExecutionLog.execution_id == execution_id
    ).order_by(AutomationExecutionLog.timestamp).all()

# --- Approvals ---
@router.get("/approvals", response_model=List[AutomationApprovalResponse])
def list_approvals(
    status: Optional[str] = Query(None),
    execution_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List human-in-the-loop pending or historical approvals."""
    query = db.query(AutomationApproval)
    if status:
        query = query.filter(AutomationApproval.status == status)
    if execution_id:
        query = query.filter(AutomationApproval.execution_id == execution_id)
    return query.order_by(desc(AutomationApproval.created_at)).all()

@router.post("/approvals/{approval_id}/decision", response_model=AutomationApprovalResponse)
def make_approval_decision(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit approval decision (APPROVED / REJECTED) and resume workflow if approved."""
    try:
        approval = automation_engine_service.process_approval_decision(
            db=db,
            approval_id=approval_id,
            decision=payload.decision,
            decision_by_id=current_user.id,
            comments=payload.comments,
        )
        return approval
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# --- AI Assistant Generator ---
@router.post("/assistant/generate", response_model=AIWorkflowGenerateResponse)
def generate_workflow_from_prompt(
    payload: AIWorkflowGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate structured workflow definition from natural language prompt."""
    return automation_engine_service.generate_ai_workflow(payload)
