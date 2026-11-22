import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.ai_agent.schemas import (
    AIAgentResponse,
    AIAgentExecutionCreate,
    AIAgentExecutionResponse,
    AIAgentExecutionStepResponse,
    AIAgentApprovalResponse,
    ApprovalDecisionRequest,
    AIPersistentPreferenceResponse,
    AIPersistentPreferenceUpdate,
)
from app.ai_agent import service

router = APIRouter(prefix="/ai-agent", tags=["AI Autonomous Agents & Orchestration"])

def serialize_execution(e) -> AIAgentExecutionResponse:
    steps_data = [
        AIAgentExecutionStepResponse(
            id=s.id,
            step_index=s.step_index,
            description=s.description,
            tool_name=s.tool_name,
            arguments=json.loads(s.arguments_json or "{}"),
            requires_approval=s.requires_approval,
            status=s.status,
            result=json.loads(s.result_json) if s.result_json else None,
            error_message=s.error_message,
            created_at=s.created_at,
            completed_at=s.completed_at,
        )
        for s in e.steps
    ]
    approvals_data = [
        AIAgentApprovalResponse(
            id=a.id,
            execution_id=a.execution_id,
            step_id=a.step_id,
            action_type=a.action_type,
            reason=a.reason,
            target_resource=a.target_resource,
            proposed_payload=json.loads(a.proposed_payload_json or "{}"),
            status=a.status,
            resolved_at=a.resolved_at,
            created_at=a.created_at,
        )
        for a in e.approvals
        if a.status == "PENDING"
    ]

    return AIAgentExecutionResponse(
        id=e.id,
        agent_id=e.agent_id,
        agent_name=e.agent.name if e.agent else e.agent_id,
        prompt=e.prompt,
        status=e.status,
        current_step_index=e.current_step_index,
        total_steps=e.total_steps,
        error_message=e.error_message,
        tokens_used=e.tokens_used,
        cost_estimate_cents=e.cost_estimate_cents,
        steps=steps_data,
        pending_approvals=approvals_data,
        created_at=e.created_at,
        completed_at=e.completed_at,
    )

@router.get("/agents", response_model=List[AIAgentResponse])
def list_agents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List available autonomous productivity agents and their authorized capabilities."""
    agents = service.get_all_agents(db)
    return [
        AIAgentResponse(
            id=a.id,
            name=a.name,
            description=a.description,
            agent_type=a.agent_type,
            model_name=a.model_name,
            tools=json.loads(a.tools_json or "[]"),
            is_system=a.is_system,
            created_at=a.created_at,
        )
        for a in agents
    ]

@router.get("/agents/{agent_id}", response_model=AIAgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve detailed agent specifications, tools, and system prompt."""
    agent = service.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")
    return AIAgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        agent_type=agent.agent_type,
        model_name=agent.model_name,
        tools=json.loads(agent.tools_json or "[]"),
        is_system=agent.is_system,
        created_at=agent.created_at,
    )

@router.post("/executions", response_model=AIAgentExecutionResponse, status_code=status.HTTP_201_CREATED)
def create_execution(
    payload: AIAgentExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Launch agent execution: generates structured plan and begins automated execution."""
    try:
        execution = service.create_agent_execution(
            db=db,
            user_id=current_user.id,
            agent_id=payload.agent_id,
            prompt=payload.prompt,
            workspace_id=payload.workspace_id,
            auto_execute_safe=payload.auto_execute_safe,
        )
        return serialize_execution(execution)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/executions", response_model=List[AIAgentExecutionResponse])
def list_executions(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List execution history and real-time status of all agent runs."""
    executions = service.list_user_executions(db, user_id=current_user.id, limit=limit)
    return [serialize_execution(e) for e in executions]

@router.get("/executions/{execution_id}", response_model=AIAgentExecutionResponse)
def get_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get real-time agent execution telemetry, plan steps, and approval gates."""
    execution = service.get_execution_details(db, execution_id=execution_id, user_id=current_user.id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found.")
    return serialize_execution(execution)

@router.post("/executions/{execution_id}/approve", response_model=AIAgentExecutionResponse)
def approve_execution_action(
    execution_id: str,
    approval_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Explicitly approve a sensitive agent action (e.g. task deletion) and resume plan."""
    try:
        updated = service.handle_approval_decision(
            db=db,
            execution_id=execution_id,
            approval_id=approval_id,
            decision="APPROVED",
            user_id=current_user.id,
        )
        return serialize_execution(updated)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/executions/{execution_id}/reject", response_model=AIAgentExecutionResponse)
def reject_execution_action(
    execution_id: str,
    approval_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a proposed action, skipping the step and preventing unwanted mutations."""
    try:
        updated = service.handle_approval_decision(
            db=db,
            execution_id=execution_id,
            approval_id=approval_id,
            decision="REJECTED",
            user_id=current_user.id,
        )
        return serialize_execution(updated)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/executions/{execution_id}/cancel", response_model=AIAgentExecutionResponse)
def cancel_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Immediately halt and cancel a running agent execution."""
    try:
        cancelled = service.cancel_execution(db, execution_id=execution_id, user_id=current_user.id)
        return serialize_execution(cancelled)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/preferences", response_model=AIPersistentPreferenceResponse)
def get_preferences(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get persistent user preferences and AI memory controls."""
    pref = service.get_or_create_user_preferences(db, current_user.id)
    return AIPersistentPreferenceResponse(
        planning_style=pref.planning_style,
        preferred_work_hours=pref.preferred_work_hours,
        summary_format=pref.summary_format,
        prioritization_approach=pref.prioritization_approach,
        personalization_enabled=pref.personalization_enabled,
        updated_at=pref.updated_at,
    )

@router.put("/preferences", response_model=AIPersistentPreferenceResponse)
def update_preferences(
    payload: AIPersistentPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update AI personalization parameters, planning style, and daily hours target."""
    pref = service.update_user_preferences(
        db,
        user_id=current_user.id,
        planning_style=payload.planning_style,
        preferred_work_hours=payload.preferred_work_hours,
        summary_format=payload.summary_format,
        prioritization_approach=payload.prioritization_approach,
        personalization_enabled=payload.personalization_enabled,
    )
    return AIPersistentPreferenceResponse(
        planning_style=pref.planning_style,
        preferred_work_hours=pref.preferred_work_hours,
        summary_format=pref.summary_format,
        prioritization_approach=pref.prioritization_approach,
        personalization_enabled=pref.personalization_enabled,
        updated_at=pref.updated_at,
    )
