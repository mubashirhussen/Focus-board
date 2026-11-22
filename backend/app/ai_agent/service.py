import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.ai_agent import (
    AIAgent,
    AIAgentExecution,
    AIAgentExecutionStep,
    AIAgentApproval,
    AIPersistentPreference,
)
from app.ai_agent.agents import seed_system_agents
from app.ai_agent.planner import construct_agent_plan
from app.ai_agent.execution_engine import run_execution_engine

def utc_now():
    return datetime.now(timezone.utc)

def get_all_agents(db: Session) -> List[AIAgent]:
    seed_system_agents(db)
    return db.query(AIAgent).filter(AIAgent.is_active == True).all()

def get_agent_by_id(db: Session, agent_id: str) -> Optional[AIAgent]:
    seed_system_agents(db)
    return db.query(AIAgent).filter(AIAgent.id == agent_id, AIAgent.is_active == True).first()

def get_or_create_user_preferences(db: Session, user_id: int) -> AIPersistentPreference:
    pref = db.query(AIPersistentPreference).filter(AIPersistentPreference.user_id == user_id).first()
    if not pref:
        pref = AIPersistentPreference(
            user_id=user_id,
            planning_style="balanced",
            preferred_work_hours=6,
            summary_format="bullet_points",
            prioritization_approach="deadline_first",
            personalization_enabled=True,
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref

def update_user_preferences(
    db: Session,
    user_id: int,
    planning_style: Optional[str] = None,
    preferred_work_hours: Optional[int] = None,
    summary_format: Optional[str] = None,
    prioritization_approach: Optional[str] = None,
    personalization_enabled: Optional[bool] = None,
) -> AIPersistentPreference:
    pref = get_or_create_user_preferences(db, user_id)
    if planning_style:
        pref.planning_style = planning_style
    if preferred_work_hours is not None:
        pref.preferred_work_hours = preferred_work_hours
    if summary_format:
        pref.summary_format = summary_format
    if prioritization_approach:
        pref.prioritization_approach = prioritization_approach
    if personalization_enabled is not None:
        pref.personalization_enabled = personalization_enabled
    db.commit()
    db.refresh(pref)
    return pref

def create_agent_execution(
    db: Session,
    user_id: int,
    agent_id: str,
    prompt: str,
    workspace_id: Optional[int] = None,
    auto_execute_safe: bool = True,
) -> AIAgentExecution:
    agent = get_agent_by_id(db, agent_id)
    if not agent:
        raise ValueError(f"Agent '{agent_id}' does not exist.")

    user_pref = get_or_create_user_preferences(db, user_id)
    plan_steps = construct_agent_plan(
        db=db,
        agent=agent,
        user_id=user_id,
        workspace_id=workspace_id,
        prompt=prompt,
        user_pref=user_pref,
    )

    execution = AIAgentExecution(
        user_id=user_id,
        workspace_id=workspace_id,
        agent_id=agent.id,
        prompt=prompt,
        status="PLANNING",
        plan_json=json.dumps(plan_steps),
        current_step_index=0,
        total_steps=len(plan_steps),
        tokens_used=50,
        cost_estimate_cents=1,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # Persist steps
    for s in plan_steps:
        step = AIAgentExecutionStep(
            execution_id=execution.id,
            step_index=s["step_index"],
            description=s["description"],
            tool_name=s["tool_name"],
            arguments_json=json.dumps(s.get("arguments", {})),
            requires_approval=s.get("requires_approval", False),
            status="PENDING",
        )
        db.add(step)
    db.commit()

    # Trigger execution engine
    return run_execution_engine(db, execution.id, auto_execute_safe=auto_execute_safe)

def list_user_executions(db: Session, user_id: int, limit: int = 20) -> List[AIAgentExecution]:
    return (
        db.query(AIAgentExecution)
        .filter(AIAgentExecution.user_id == user_id)
        .order_by(AIAgentExecution.created_at.desc())
        .limit(limit)
        .all()
    )

def get_execution_details(db: Session, execution_id: str, user_id: int) -> Optional[AIAgentExecution]:
    return (
        db.query(AIAgentExecution)
        .filter(AIAgentExecution.id == execution_id, AIAgentExecution.user_id == user_id)
        .first()
    )

def handle_approval_decision(
    db: Session,
    execution_id: str,
    approval_id: str,
    decision: str,  # "APPROVED" or "REJECTED"
    user_id: int,
) -> AIAgentExecution:
    execution = get_execution_details(db, execution_id, user_id)
    if not execution:
        raise ValueError("Execution not found or access denied.")

    approval = (
        db.query(AIAgentApproval)
        .filter(AIAgentApproval.id == approval_id, AIAgentApproval.execution_id == execution_id)
        .first()
    )
    if not approval or approval.status != "PENDING":
        raise ValueError("Invalid or already resolved approval request.")

    approval.status = decision.upper()
    approval.resolved_at = utc_now()

    # Find the corresponding step
    step = db.query(AIAgentExecutionStep).filter(AIAgentExecutionStep.id == approval.step_id).first()
    if step:
        if decision.upper() == "APPROVED":
            step.status = "APPROVED"
        else:
            step.status = "SKIPPED"
            step.error_message = "Action rejected by user."

    db.commit()

    # Resume execution engine
    return run_execution_engine(db, execution_id, auto_execute_safe=True)

def cancel_execution(db: Session, execution_id: str, user_id: int) -> AIAgentExecution:
    execution = get_execution_details(db, execution_id, user_id)
    if not execution:
        raise ValueError("Execution not found or access denied.")

    if execution.status in ["COMPLETED", "FAILED", "CANCELLED"]:
        return execution

    execution.status = "CANCELLED"
    # Mark any pending approvals as cancelled
    pending_apprs = (
        db.query(AIAgentApproval)
        .filter(AIAgentApproval.execution_id == execution_id, AIAgentApproval.status == "PENDING")
        .all()
    )
    for a in pending_apprs:
        a.status = "CANCELLED"
        a.resolved_at = utc_now()

    db.commit()
    db.refresh(execution)
    return execution
