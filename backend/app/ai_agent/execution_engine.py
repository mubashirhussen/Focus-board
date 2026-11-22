import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.ai_agent import AIAgentExecution, AIAgentExecutionStep, AIAgentApproval
from app.ai_agent.tools import TOOL_REGISTRY

def utc_now():
    return datetime.now(timezone.utc)

def run_execution_engine(db: Session, execution_id: str, auto_execute_safe: bool = True) -> AIAgentExecution:
    """
    Step-by-step orchestrator for AI Agent execution.
    Executes safe steps; halts at steps requiring human approval.
    """
    execution = db.query(AIAgentExecution).filter(AIAgentExecution.id == execution_id).first()
    if not execution:
        raise ValueError(f"Execution {execution_id} not found")

    if execution.status in ["COMPLETED", "FAILED", "CANCELLED"]:
        return execution

    steps = (
        db.query(AIAgentExecutionStep)
        .filter(AIAgentExecutionStep.execution_id == execution_id)
        .order_by(AIAgentExecutionStep.step_index.asc())
        .all()
    )

    execution.status = "RUNNING"
    db.commit()

    for step in steps:
        if step.status == "COMPLETED" or step.status == "SKIPPED":
            continue

        tool_def = TOOL_REGISTRY.get(step.tool_name)
        if not tool_def:
            step.status = "FAILED"
            step.error_message = f"Tool '{step.tool_name}' not registered in tool registry."
            execution.status = "FAILED"
            execution.error_message = step.error_message
            db.commit()
            return execution

        # Check if step requires approval and has NOT been approved yet
        if step.requires_approval and step.status != "APPROVED":
            step.status = "AWAITING_APPROVAL"
            execution.status = "AWAITING_APPROVAL"

            # Create or find pending approval record
            existing_appr = (
                db.query(AIAgentApproval)
                .filter(AIAgentApproval.execution_id == execution_id, AIAgentApproval.step_id == step.id)
                .first()
            )
            if not existing_appr:
                approval = AIAgentApproval(
                    execution_id=execution_id,
                    step_id=step.id,
                    user_id=execution.user_id,
                    action_type="DESTRUCTIVE_ACTION" if "delete" in step.tool_name else "SENSITIVE_ACTION",
                    reason=f"Agent requested to execute '{step.tool_name}': {step.description}",
                    target_resource=step.arguments_json,
                    proposed_payload_json=step.arguments_json,
                    status="PENDING",
                )
                db.add(approval)
            db.commit()
            # Halt execution here until human approval
            return execution

        # Step is safe or has been approved -> Execute!
        if auto_execute_safe or step.status == "APPROVED":
            step.status = "RUNNING"
            db.commit()

            try:
                args = json.loads(step.arguments_json or "{}")
                result = tool_def.execute(
                    db=db,
                    user_id=execution.user_id,
                    workspace_id=execution.workspace_id,
                    args=args,
                )
                step.result_json = json.dumps(result)
                step.status = "COMPLETED"
                step.completed_at = utc_now()
                execution.current_step_index = step.step_index + 1
                execution.tokens_used += 120  # Telemetry simulation based on prompt & result
                execution.cost_estimate_cents += 1
            except Exception as exc:
                step.status = "FAILED"
                step.error_message = str(exc)
                execution.status = "FAILED"
                execution.error_message = f"Step {step.step_index} failed: {exc}"
                db.commit()
                return execution

    # All steps completed
    all_done = all(s.status in ["COMPLETED", "SKIPPED"] for s in steps)
    if all_done:
        execution.status = "COMPLETED"
        execution.completed_at = utc_now()

    db.commit()
    db.refresh(execution)
    return execution
