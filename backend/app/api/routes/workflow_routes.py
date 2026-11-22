import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.workflow import Workflow, WorkflowExecution
from app.schemas.workflow import WorkflowCreate, WorkflowResponse, WorkflowExecutionResponse
from app.api.dependencies import get_current_user
from app.services.entitlement_service import get_tenant_id_for_user
from app.services.workflow_engine import workflow_engine

router = APIRouter(prefix="/workflows", tags=["Workflow Automation"])

@router.get("", response_model=List[WorkflowResponse])
def get_workflows(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List automation workflows configured for tenant or user."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    workflows = db.query(Workflow).filter(
        (Workflow.tenant_id == tenant_id) | (Workflow.user_id == current_user.id)
    ).all()

    results = []
    for w in workflows:
        results.append(WorkflowResponse(
            id=w.id,
            tenant_id=w.tenant_id,
            name=w.name,
            description=w.description,
            trigger_type=w.trigger_type,
            trigger_config=json.loads(w.trigger_config_json) if w.trigger_config_json else {},
            conditions=json.loads(w.conditions_json) if w.conditions_json else [],
            actions=json.loads(w.actions_json) if w.actions_json else [],
            is_active=w.is_active,
            execution_count=w.execution_count,
            created_at=w.created_at,
            updated_at=w.updated_at,
        ))
    return results

@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_workflow(
    workflow_in: WorkflowCreate,
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new event-driven productivity workflow."""
    tenant_id = get_tenant_id_for_user(current_user.id, workspace_id)
    w = Workflow(
        tenant_id=tenant_id,
        user_id=current_user.id,
        name=workflow_in.name,
        description=workflow_in.description,
        trigger_type=workflow_in.trigger_type,
        trigger_config_json=json.dumps(workflow_in.trigger_config),
        conditions_json=json.dumps(workflow_in.conditions),
        actions_json=json.dumps(workflow_in.actions),
        is_active=workflow_in.is_active,
    )
    db.add(w)
    db.commit()
    db.refresh(w)

    return WorkflowResponse(
        id=w.id,
        tenant_id=w.tenant_id,
        name=w.name,
        description=w.description,
        trigger_type=w.trigger_type,
        trigger_config=workflow_in.trigger_config,
        conditions=workflow_in.conditions,
        actions=workflow_in.actions,
        is_active=w.is_active,
        execution_count=w.execution_count,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )

@router.patch("/{workflow_id}/toggle", response_model=WorkflowResponse)
def toggle_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle active state of an automation workflow."""
    w = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    w.is_active = not w.is_active
    db.commit()
    db.refresh(w)

    return WorkflowResponse(
        id=w.id,
        tenant_id=w.tenant_id,
        name=w.name,
        description=w.description,
        trigger_type=w.trigger_type,
        trigger_config=json.loads(w.trigger_config_json) if w.trigger_config_json else {},
        conditions=json.loads(w.conditions_json) if w.conditions_json else [],
        actions=json.loads(w.actions_json) if w.actions_json else [],
        is_active=w.is_active,
        execution_count=w.execution_count,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )

@router.delete("/{workflow_id}", status_code=status.HTTP_200_OK)
def delete_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permanently delete an automation workflow."""
    w = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    db.delete(w)
    db.commit()
    return {"message": "Workflow deleted successfully"}

@router.post("/{workflow_id}/test")
def test_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Simulate execution of an automation workflow."""
    w = db.query(Workflow).filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    res = workflow_engine._execute_workflow(db, w, {"priority": "High", "status": "Todo"}, depth=0)
    return res
