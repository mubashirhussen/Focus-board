import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.workflow import Workflow, WorkflowExecution
from app.models.notification import Notification

logger = logging.getLogger("focusboard.workflow")

MAX_EXECUTION_DEPTH = 3

class WorkflowEngine:
    """
    Lightweight, deterministic event-driven workflow automation engine.
    Matches event triggers against registered tenant workflows with recursion protection.
    """
    def trigger_event(
        self,
        db: Session,
        tenant_id: str,
        user_id: int,
        event_name: str,
        payload: Dict[str, Any],
        depth: int = 0
    ) -> List[Dict[str, Any]]:
        if depth >= MAX_EXECUTION_DEPTH:
            logger.warning(f"Workflow recursion depth limit ({MAX_EXECUTION_DEPTH}) reached for tenant {tenant_id}. Stopping propagation.")
            return []

        # Find active workflows for tenant or user matching trigger_type
        workflows = db.query(Workflow).filter(
            Workflow.trigger_type == event_name,
            Workflow.is_active == True,
            (Workflow.tenant_id == tenant_id) | (Workflow.user_id == user_id)
        ).all()

        results = []
        for wf in workflows:
            res = self._execute_workflow(db, wf, payload, depth)
            results.append(res)

        return results

    def _execute_workflow(
        self,
        db: Session,
        workflow: Workflow,
        payload: Dict[str, Any],
        depth: int
    ) -> Dict[str, Any]:
        conditions = json.loads(workflow.conditions_json) if workflow.conditions_json else []
        actions = json.loads(workflow.actions_json) if workflow.actions_json else []

        # 1. Condition evaluation
        for cond in conditions:
            field = cond.get("field")
            op = cond.get("op", "==")
            val = cond.get("value")
            actual_val = payload.get(field)

            if op == "==" and actual_val != val:
                return {"workflow_id": workflow.id, "status": "skipped", "reason": "condition_not_met"}
            elif op == "!=" and actual_val == val:
                return {"workflow_id": workflow.id, "status": "skipped", "reason": "condition_not_met"}

        # 2. Action execution
        executed_actions = []
        try:
            for action in actions:
                action_type = action.get("type")
                if action_type == "create_notification":
                    title = action.get("title", f"Workflow Alert: {workflow.name}")
                    message = action.get("message", f"Triggered by {workflow.trigger_type}")
                    notif = Notification(
                        user_id=workflow.user_id,
                        type="SYSTEM",
                        title=title,
                        message=message,
                        scheduled_at=datetime.now(timezone.utc),
                        status="SENT",
                        delivery_channel="IN_APP",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    db.add(notif)
                    executed_actions.append(f"Notification created: {title}")

                elif action_type == "log_activity":
                    executed_actions.append(f"Activity logged: {action.get('message', 'Workflow ran')}")

            workflow.execution_count += 1
            now = datetime.now(timezone.utc)

            execution = WorkflowExecution(
                workflow_id=workflow.id,
                trigger_event=workflow.trigger_type,
                status="success",
                result_details=json.dumps(executed_actions),
                created_at=now,
            )
            db.add(execution)
            db.commit()

            return {
                "workflow_id": workflow.id,
                "status": "success",
                "actions": executed_actions,
            }
        except Exception as exc:
            db.rollback()
            logger.error(f"Workflow {workflow.id} execution failed: {exc}")
            now = datetime.now(timezone.utc)
            execution = WorkflowExecution(
                workflow_id=workflow.id,
                trigger_event=workflow.trigger_type,
                status="failed",
                result_details=str(exc),
                created_at=now,
            )
            db.add(execution)
            db.commit()
            return {"workflow_id": workflow.id, "status": "failed", "error": str(exc)}

workflow_engine = WorkflowEngine()
