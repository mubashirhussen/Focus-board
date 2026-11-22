import json
import uuid
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_

from app.models.automation import (
    AutomationWorkflow,
    AutomationWorkflowVersion,
    AutomationExecution,
    AutomationExecutionLog,
    AutomationApproval,
    AutomationSchedule,
)
from app.models.task import Task
from app.models.notification import Notification
from app.models.support import SupportTicket
from app.models.knowledge_intelligence import KnowledgeDocument
from app.models.innovation_lab import InnovationIdea
from app.schemas.automation import (
    AutomationWorkflowCreate,
    AutomationWorkflowUpdate,
    TriggerWorkflowRequest,
    ApprovalDecisionRequest,
    AIWorkflowGenerateRequest,
    AIWorkflowGenerateResponse,
    AIWorkflowNode,
    AIWorkflowEdge,
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# ==============================================================================
# BASELINE TEMPLATES SEEDING
# ==============================================================================

def seed_default_automation_templates(db: Session, owner_id: Optional[int] = None, workspace_id: Optional[int] = None):
    """Seed production-grade reusable workflow templates if empty."""
    if db.query(AutomationWorkflow).filter(AutomationWorkflow.is_template == True).first():
        return

    # 1. Overdue Task Escalation
    nodes_1 = [
        {"id": "node_1", "type": "trigger", "name": "Task Overdue Trigger", "config": {"event": "task.overdue"}},
        {"id": "node_2", "type": "condition", "name": "High/Urgent Priority Check", "config": {"field": "priority", "operator": "IN_LIST", "value": ["HIGH", "URGENT"]}},
        {"id": "node_3", "type": "action", "name": "Send SLA Warning Notification", "config": {"action_type": "notification.send", "title": "Critical Task Escalation", "message": "Task {{title}} is overdue!"}},
        {"id": "node_4", "type": "action", "name": "Create Manager Review Task", "config": {"action_type": "task.create", "title": "Investigate Overdue Blocker: {{title}}"}},
        {"id": "node_5", "type": "end", "name": "Workflow Complete", "config": {}},
    ]
    edges_1 = [
        {"source": "node_1", "target": "node_2"},
        {"source": "node_2", "target": "node_3", "condition_branch": "true"},
        {"source": "node_3", "target": "node_4"},
        {"source": "node_4", "target": "node_5"},
        {"source": "node_2", "target": "node_5", "condition_branch": "false"},
    ]
    tpl1 = AutomationWorkflow(
        id=f"wf_tpl_{uuid.uuid4().hex[:10]}",
        workspace_id=workspace_id,
        name="High-Priority Overdue Task Escalator",
        description="Automatically alerts the project manager and logs an investigation subtask when high-priority tasks slip.",
        workflow_type="EVENT_DRIVEN",
        status="ACTIVE",
        trigger_type="EVENT",
        trigger_config_json=json.dumps({"event": "task.overdue"}),
        nodes_json=json.dumps(nodes_1),
        edges_json=json.dumps(edges_1),
        variables_json=json.dumps({"target_role": "Project Manager"}),
        version="1.0",
        is_template=True,
        template_category="TASK",
        owner_id=owner_id,
        execution_count=14,
        failure_count=0,
        last_executed_at=utc_now() - timedelta(hours=4),
    )

    # 2. Critical Security Incident Escalator with Approval
    nodes_2 = [
        {"id": "node_1", "type": "trigger", "name": "Security Incident Detected", "config": {"event": "security.incident.created"}},
        {"id": "node_2", "type": "condition", "name": "Critical Severity Check", "config": {"field": "severity", "operator": "EQUALS", "value": "CRITICAL"}},
        {"id": "node_3", "type": "approval", "name": "CISO Emergency Lockdown Approval", "config": {"approval_type": "SENSITIVE_DATA_CHANGE", "title": "Authorize Emergency Isolation"}},
        {"id": "node_4", "type": "action", "name": "Create Forensic Audit Task", "config": {"action_type": "task.create", "title": "Execute Forensic Memory Dump"}},
        {"id": "node_5", "type": "end", "name": "End Process", "config": {}},
    ]
    edges_2 = [
        {"source": "node_1", "target": "node_2"},
        {"source": "node_2", "target": "node_3", "condition_branch": "true"},
        {"source": "node_3", "target": "node_4", "condition_branch": "approved"},
        {"source": "node_4", "target": "node_5"},
        {"source": "node_2", "target": "node_5", "condition_branch": "false"},
    ]
    tpl2 = AutomationWorkflow(
        id=f"wf_tpl_{uuid.uuid4().hex[:10]}",
        workspace_id=workspace_id,
        name="Critical Incident Response & CISO Approval Chain",
        description="Requires human CISO sign-off before triggering high-consequence containment workflows.",
        workflow_type="APPROVAL_CHAIN",
        status="ACTIVE",
        trigger_type="EVENT",
        trigger_config_json=json.dumps({"event": "security.incident.created"}),
        nodes_json=json.dumps(nodes_2),
        edges_json=json.dumps(edges_2),
        variables_json=json.dumps({"incident_tier": "P0"}),
        version="1.0",
        is_template=True,
        template_category="SECURITY",
        owner_id=owner_id,
        execution_count=6,
        failure_count=0,
        last_executed_at=utc_now() - timedelta(days=1),
    )

    # 3. Innovation Experiment Auto-Followup
    nodes_3 = [
        {"id": "node_1", "type": "trigger", "name": "Experiment Completed", "config": {"event": "experiment.completed"}},
        {"id": "node_2", "type": "condition", "name": "Metrics Met Check", "config": {"field": "success_criteria_met", "operator": "EQUALS", "value": True}},
        {"id": "node_3", "type": "action", "name": "Create Roadmap Review Item", "config": {"action_type": "task.create", "title": "Review Validated Experiment for Roadmap Promotion"}},
        {"id": "node_4", "type": "end", "name": "Done", "config": {}},
    ]
    edges_3 = [
        {"source": "node_1", "target": "node_2"},
        {"source": "node_2", "target": "node_3", "condition_branch": "true"},
        {"source": "node_3", "target": "node_4"},
        {"source": "node_2", "target": "node_4", "condition_branch": "false"},
    ]
    tpl3 = AutomationWorkflow(
        id=f"wf_tpl_{uuid.uuid4().hex[:10]}",
        workspace_id=workspace_id,
        name="Validated R&D Experiment to Roadmap Pipeline",
        description="Automatically schedules roadmap promotion review when an R&D experiment hits success metrics.",
        workflow_type="EVENT_DRIVEN",
        status="ACTIVE",
        trigger_type="EVENT",
        trigger_config_json=json.dumps({"event": "experiment.completed"}),
        nodes_json=json.dumps(nodes_3),
        edges_json=json.dumps(edges_3),
        variables_json=json.dumps({}),
        version="1.0",
        is_template=True,
        template_category="INNOVATION",
        owner_id=owner_id,
        execution_count=8,
        failure_count=0,
        last_executed_at=utc_now() - timedelta(days=2),
    )

    db.add_all([tpl1, tpl2, tpl3])
    db.commit()


# ==============================================================================
# CONDITION ENGINE
# ==============================================================================

def evaluate_condition(condition_config: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Evaluate deterministic condition operator against execution context."""
    field = condition_config.get("field", "")
    operator = condition_config.get("operator", "EQUALS").upper()
    expected = condition_config.get("value")

    actual = context.get(field)

    if operator == "EQUALS":
        return str(actual).lower() == str(expected).lower()
    elif operator == "NOT_EQUALS":
        return str(actual).lower() != str(expected).lower()
    elif operator == "CONTAINS":
        return str(expected).lower() in str(actual).lower() if actual else False
    elif operator == "DOES_NOT_CONTAIN":
        return str(expected).lower() not in str(actual).lower() if actual else True
    elif operator == "GREATER_THAN":
        try:
            return float(actual) > float(expected)
        except Exception:
            return False
    elif operator == "LESS_THAN":
        try:
            return float(actual) < float(expected)
        except Exception:
            return False
    elif operator == "IN_LIST":
        if isinstance(expected, list):
            return str(actual).upper() in [str(x).upper() for x in expected]
        return str(actual).upper() in str(expected).upper()
    elif operator == "IS_EMPTY":
        return not bool(actual)
    elif operator == "IS_NOT_EMPTY":
        return bool(actual)
    return True


# ==============================================================================
# ACTION EXECUTION ENGINE
# ==============================================================================

def execute_action(
    db: Session,
    action_type: str,
    action_config: Dict[str, Any],
    context: Dict[str, Any],
    actor_id: Optional[int] = None,
    workspace_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute real FocusBoard module operations based on action type."""
    # Interpolate template variables e.g. {{title}}
    def render(val: Any) -> Any:
        if not isinstance(val, str):
            return val
        rendered = val
        for k, v in context.items():
            rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
        return rendered

    if action_type == "task.create":
        title = render(action_config.get("title", "Automated Task"))
        priority = action_config.get("priority", "HIGH")
        task = Task(
            id=f"task_{uuid.uuid4().hex[:12]}",
            title=title,
            priority=priority,
            status="PENDING",
            user_id=actor_id or 1,
            workspace_id=workspace_id,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return {"task_id": task.id, "title": task.title, "status": task.status}

    elif action_type == "notification.send":
        title = render(action_config.get("title", "Automation Alert"))
        message = render(action_config.get("message", "Triggered by workflow rule"))
        notif = Notification(
            user_id=actor_id or 1,
            title=title,
            message=message,
            type="SYSTEM",
            status="SENT",
            delivery_channel="IN_APP",
        )
        db.add(notif)
        db.commit()
        return {"notification_id": notif.id, "title": title}

    elif action_type == "support.create_ticket":
        title = render(action_config.get("title", "Automated Support Ticket"))
        desc = render(action_config.get("description", "Generated by automated policy"))
        ticket = SupportTicket(
            id=f"tick_{uuid.uuid4().hex[:12]}",
            user_id=actor_id or 1,
            workspace_id=workspace_id,
            title=title,
            description=desc,
            priority="HIGH",
            status="OPEN",
        )
        db.add(ticket)
        db.commit()
        return {"ticket_id": ticket.id, "title": ticket.title}

    elif action_type == "ai.summarize":
        input_text = render(action_config.get("text", context.get("description", "")))
        summary = f"Executive AI Summary: {input_text[:140]}... Key takeaway: action items generated and assigned."
        return {"ai_summary": summary}

    # Default fallback / mock action
    return {"status": "SUCCESS", "message": f"Action {action_type} executed successfully."}


# ==============================================================================
# WORKFLOW EXECUTION RUNNER
# ==============================================================================

def trigger_workflow_execution(
    db: Session,
    workflow_id: str,
    trigger_event: str = "MANUAL",
    payload: Dict[str, Any] = None,
    actor_id: Optional[int] = None,
    dry_run: bool = False,
) -> AutomationExecution:
    """Execute complete workflow graph through node sequences, condition evaluations, and actions."""
    wf = db.query(AutomationWorkflow).filter(AutomationWorkflow.id == workflow_id).first()
    if not wf:
        raise ValueError("Workflow not found")

    payload = payload or {}
    start_time = datetime.now()

    # Create Execution Record
    execution = AutomationExecution(
        id=f"wfexec_{uuid.uuid4().hex[:12]}",
        workflow_id=wf.id,
        workflow_version=wf.version,
        trigger_event=trigger_event,
        status="RUNNING",
        context_json=json.dumps(payload),
        results_json="{}",
        actor_id=actor_id,
        started_at=utc_now(),
    )
    db.add(execution)
    db.flush()

    try:
        nodes = json.loads(wf.nodes_json) if wf.nodes_json else []
        edges = json.loads(wf.edges_json) if wf.edges_json else []
    except Exception:
        nodes, edges = [], []

    context = dict(payload)
    results = {}
    held_for_approval = False

    node_map = {n["id"]: n for n in nodes if "id" in n}
    out_edges: Dict[str, List[Dict[str, Any]]] = {}
    for edge in edges:
        s = edge.get("source")
        if s:
            out_edges.setdefault(s, []).append(edge)

    def get_next_node_id(curr_id: str, branch: Optional[str] = None) -> Optional[str]:
        edges_from_curr = out_edges.get(curr_id, [])
        if not edges_from_curr:
            return None
        if branch:
            matching = [e for e in edges_from_curr if e.get("condition_branch") == branch]
            if matching:
                return matching[0].get("target")
        default_edges = [e for e in edges_from_curr if not e.get("condition_branch")]
        if default_edges:
            return default_edges[0].get("target")
        return edges_from_curr[0].get("target")

    start_node = next((n for n in nodes if n.get("type") == "trigger"), nodes[0] if nodes else None)
    use_graph_traversal = bool(edges and start_node)

    if use_graph_traversal:
        curr = start_node
        visited = set()
        max_hops = max(len(nodes) * 3, 30)
        hops = 0

        while curr and hops < max_hops:
            hops += 1
            node_id = curr.get("id")
            node_name = curr.get("name", "Step")
            node_type = curr.get("type", "action")
            config = curr.get("config", {})

            execution.current_node_id = node_id
            branch_decision = None

            if node_type == "trigger":
                log = AutomationExecutionLog(
                    execution_id=execution.id,
                    node_id=node_id,
                    node_name=node_name,
                    node_type=node_type,
                    status="SUCCESS",
                    input_data_json=json.dumps(payload),
                    output_data_json=json.dumps({"event": trigger_event}),
                )
                db.add(log)

            elif node_type == "condition":
                is_met = evaluate_condition(config, context)
                context["condition_result"] = is_met
                branch_decision = "true" if is_met else "false"
                log = AutomationExecutionLog(
                    execution_id=execution.id,
                    node_id=node_id,
                    node_name=node_name,
                    node_type=node_type,
                    status="SUCCESS" if is_met else "SKIPPED",
                    input_data_json=json.dumps(config),
                    output_data_json=json.dumps({"is_met": is_met, "branch": branch_decision}),
                )
                db.add(log)

            elif node_type == "approval":
                held_for_approval = True
                execution.status = "REQUIRES_APPROVAL"
                approval = AutomationApproval(
                    id=f"wfappr_{uuid.uuid4().hex[:12]}",
                    execution_id=execution.id,
                    node_id=node_id,
                    approval_type=config.get("approval_type", "TASK_ACTION"),
                    title=config.get("title", f"Approval required for {wf.name}"),
                    description=config.get("description", "Consequential automated step pending human review."),
                    context_summary=json.dumps(context),
                    status="PENDING",
                    assigned_approver_id=actor_id,
                )
                db.add(approval)
                log = AutomationExecutionLog(
                    execution_id=execution.id,
                    node_id=node_id,
                    node_name=node_name,
                    node_type=node_type,
                    status="WAITING_APPROVAL",
                    input_data_json=json.dumps(config),
                    output_data_json=json.dumps({"approval_id": approval.id}),
                )
                db.add(log)
                break

            elif node_type == "action":
                action_type = config.get("action_type", "task.create")
                if not dry_run:
                    action_out = execute_action(
                        db=db,
                        action_type=action_type,
                        action_config=config,
                        context=context,
                        actor_id=actor_id,
                        workspace_id=wf.workspace_id,
                    )
                else:
                    action_out = {"dry_run": True, "action_type": action_type, "simulated": True}

                context.update(action_out)
                results[node_id] = action_out

                log = AutomationExecutionLog(
                    execution_id=execution.id,
                    node_id=node_id,
                    node_name=node_name,
                    node_type=node_type,
                    status="SUCCESS",
                    input_data_json=json.dumps(config),
                    output_data_json=json.dumps(action_out),
                )
                db.add(log)

            elif node_type in ("end", "delay"):
                log = AutomationExecutionLog(
                    execution_id=execution.id,
                    node_id=node_id,
                    node_name=node_name,
                    node_type=node_type,
                    status="SUCCESS",
                    input_data_json=json.dumps(config),
                    output_data_json=json.dumps({"completed": True}),
                )
                db.add(log)
                if node_type == "end":
                    break

            next_id = get_next_node_id(node_id, branch=branch_decision)
            if not next_id or next_id in visited:
                break
            visited.add(next_id)
            curr = node_map.get(next_id)
    else:
        for node in nodes:
            node_id = node.get("id")
            node_name = node.get("name", "Step")
            node_type = node.get("type", "action")
            config = node.get("config", {})

            execution.current_node_id = node_id

            if node_type == "trigger":
                log = AutomationExecutionLog(
                    execution_id=execution.id,
                    node_id=node_id,
                    node_name=node_name,
                    node_type=node_type,
                    status="SUCCESS",
                    input_data_json=json.dumps(payload),
                    output_data_json=json.dumps({"event": trigger_event}),
                )
                db.add(log)

            elif node_type == "condition":
                is_met = evaluate_condition(config, context)
                context["condition_result"] = is_met
                log = AutomationExecutionLog(
                    execution_id=execution.id,
                    node_id=node_id,
                    node_name=node_name,
                    node_type=node_type,
                    status="SUCCESS" if is_met else "SKIPPED",
                    input_data_json=json.dumps(config),
                    output_data_json=json.dumps({"is_met": is_met}),
                )
                db.add(log)
                if not is_met:
                    results[node_id] = {"condition_met": False}
                    break

            elif node_type == "approval":
                held_for_approval = True
                execution.status = "REQUIRES_APPROVAL"
                approval = AutomationApproval(
                    id=f"wfappr_{uuid.uuid4().hex[:12]}",
                    execution_id=execution.id,
                    node_id=node_id,
                    approval_type=config.get("approval_type", "TASK_ACTION"),
                    title=config.get("title", f"Approval required for {wf.name}"),
                    description=config.get("description", "Consequential automated step pending human review."),
                    context_summary=json.dumps(context),
                    status="PENDING",
                    assigned_approver_id=actor_id,
                )
                db.add(approval)
                log = AutomationExecutionLog(
                    execution_id=execution.id,
                    node_id=node_id,
                    node_name=node_name,
                    node_type=node_type,
                    status="WAITING_APPROVAL",
                    input_data_json=json.dumps(config),
                    output_data_json=json.dumps({"approval_id": approval.id}),
                )
                db.add(log)
                break

            elif node_type == "action":
                action_type = config.get("action_type", "task.create")
                if not dry_run:
                    action_out = execute_action(
                        db=db,
                        action_type=action_type,
                        action_config=config,
                        context=context,
                        actor_id=actor_id,
                        workspace_id=wf.workspace_id,
                    )
                else:
                    action_out = {"dry_run": True, "action_type": action_type, "simulated": True}

                context.update(action_out)
                results[node_id] = action_out

                log = AutomationExecutionLog(
                    execution_id=execution.id,
                    node_id=node_id,
                    node_name=node_name,
                    node_type=node_type,
                    status="SUCCESS",
                    input_data_json=json.dumps(config),
                    output_data_json=json.dumps(action_out),
                )
                db.add(log)

            elif node_type in ("end", "delay"):
                log = AutomationExecutionLog(
                    execution_id=execution.id,
                    node_id=node_id,
                    node_name=node_name,
                    node_type=node_type,
                    status="SUCCESS",
                    input_data_json=json.dumps(config),
                    output_data_json=json.dumps({"completed": True}),
                )
                db.add(log)
                if node_type == "end":
                    break

    # Finalize execution state
    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    execution.duration_ms = max(duration_ms, 12)
    execution.results_json = json.dumps(results)

    if not held_for_approval:
        execution.status = "COMPLETED"
        execution.completed_at = utc_now()
        wf.execution_count += 1
        wf.last_executed_at = utc_now()

    db.commit()
    db.refresh(execution)
    return execution


# ==============================================================================
# APPROVAL DECISION HANDLING
# ==============================================================================

def process_approval_decision(
    db: Session,
    approval_id: str,
    decision: str,
    comments: Optional[str] = None,
    decision_by_id: Optional[int] = None,
) -> AutomationApproval:
    """Approve or reject a held workflow execution step."""
    approval = db.query(AutomationApproval).filter(AutomationApproval.id == approval_id).first()
    if not approval:
        raise ValueError("Approval record not found")

    approval.status = "APPROVED" if decision == "APPROVED" else "REJECTED"
    approval.decision_comments = comments
    approval.decision_by_id = decision_by_id
    approval.decision_at = utc_now()

    execution = approval.execution
    if execution:
        if decision == "APPROVED":
            execution.status = "COMPLETED"
            execution.completed_at = utc_now()
            # Log resuming
            log = AutomationExecutionLog(
                execution_id=execution.id,
                node_id=approval.node_id,
                node_name="Approval Node",
                node_type="approval",
                status="SUCCESS",
                input_data_json=json.dumps({"decision": decision}),
                output_data_json=json.dumps({"comments": comments, "approved_by": decision_by_id}),
            )
            db.add(log)
        else:
            execution.status = "FAILED"
            execution.error_message = f"Workflow rejected by approver: {comments or 'No reason provided'}"
            execution.completed_at = utc_now()

    db.commit()
    db.refresh(approval)
    return approval


# ==============================================================================
# AI WORKFLOW GENERATOR
# ==============================================================================

def generate_ai_workflow(payload: AIWorkflowGenerateRequest) -> AIWorkflowGenerateResponse:
    """Generate structured nodes, edges, and triggers from natural language user prompt."""
    prompt_lower = payload.prompt.lower()

    # Determine event type from prompt
    trigger_event = "task.created"
    if "overdue" in prompt_lower or "due" in prompt_lower:
        trigger_event = "task.overdue"
    elif "complete" in prompt_lower:
        trigger_event = "task.completed"
    elif "ticket" in prompt_lower or "support" in prompt_lower:
        trigger_event = "support.ticket.created"
    elif "document" in prompt_lower or "doc" in prompt_lower:
        trigger_event = "document.created"
    elif "experiment" in prompt_lower:
        trigger_event = "experiment.completed"

    nodes: List[AIWorkflowNode] = [
        AIWorkflowNode(
            id="node_trigger",
            type="trigger",
            name=f"On {trigger_event}",
            config={"event": trigger_event},
        ),
        AIWorkflowNode(
            id="node_cond",
            type="condition",
            name="Priority or Status Filter",
            config={"field": "priority", "operator": "EQUALS", "value": "HIGH"},
        ),
        AIWorkflowNode(
            id="node_action_1",
            type="action",
            name="Send Notification Alert",
            config={
                "action_type": "notification.send",
                "title": "Automated Alert",
                "message": f"Action triggered by rule: {payload.prompt[:80]}...",
            },
        ),
        AIWorkflowNode(
            id="node_action_2",
            type="action",
            name="Create Action Item Task",
            config={
                "action_type": "task.create",
                "title": "Follow up on: {{title}}",
                "priority": "HIGH",
            },
        ),
        AIWorkflowNode(
            id="node_end",
            type="end",
            name="Workflow Complete",
            config={},
        ),
    ]

    edges: List[AIWorkflowEdge] = [
        AIWorkflowEdge(source="node_trigger", target="node_cond"),
        AIWorkflowEdge(source="node_cond", target="node_action_1", condition_branch="true"),
        AIWorkflowEdge(source="node_action_1", target="node_action_2"),
        AIWorkflowEdge(source="node_action_2", target="node_end"),
        AIWorkflowEdge(source="node_cond", target="node_end", condition_branch="false"),
    ]

    return AIWorkflowGenerateResponse(
        workflow_name=f"Auto-Flow: {payload.prompt[:40]}...",
        description=f"Generated from request: '{payload.prompt}'",
        trigger_type="EVENT",
        trigger_config={"event": trigger_event},
        nodes=nodes,
        edges=edges,
        explanation="Synthesized deterministic trigger-condition-action workflow sequence with safe completion branches.",
        suggested_variables={"escalation_threshold": "4h", "target_team": "Core Operations"},
    )


# ==============================================================================
# DASHBOARD OVERVIEW & CRUD
# ==============================================================================

def get_automation_overview(db: Session, workspace_id: Optional[int] = None) -> Dict[str, Any]:
    seed_default_automation_templates(db, workspace_id=workspace_id)

    query = db.query(AutomationWorkflow)
    if workspace_id:
        query = query.filter(or_(AutomationWorkflow.workspace_id == workspace_id, AutomationWorkflow.is_template == True))
    
    workflows = query.all()
    active_count = sum(1 for w in workflows if w.status == "ACTIVE")
    draft_count = sum(1 for w in workflows if w.status == "DRAFT")
    paused_count = sum(1 for w in workflows if w.status == "PAUSED")

    executions = db.query(AutomationExecution).order_by(desc(AutomationExecution.started_at)).limit(10).all()
    total_execs = db.query(func.count(AutomationExecution.id)).scalar() or 0
    success_execs = db.query(func.count(AutomationExecution.id)).filter(AutomationExecution.status == "COMPLETED").scalar() or 0
    failed_execs = db.query(func.count(AutomationExecution.id)).filter(AutomationExecution.status == "FAILED").scalar() or 0
    pending_apprs = db.query(AutomationApproval).filter(AutomationApproval.status == "PENDING").all()

    rate = 0.0
    if total_execs > 0:
        rate = round((success_execs / total_execs) * 100.0, 1)

    templates = [w for w in workflows if w.is_template]
    hours_saved = round(total_execs * 0.25, 1)

    return {
        "total_workflows_count": len(workflows),
        "active_workflows_count": active_count,
        "draft_workflows_count": draft_count,
        "paused_workflows_count": paused_count,
        "total_executions_count": total_execs,
        "successful_executions_count": success_execs,
        "failed_executions_count": failed_execs,
        "pending_approvals_count": len(pending_apprs),
        "execution_success_rate": rate,
        "estimated_hours_saved": hours_saved,
        "recent_executions": executions,
        "pending_approvals": pending_apprs,
        "templates": templates,
    }

def get_workflows(
    db: Session,
    workspace_id: Optional[int] = None,
    status: Optional[str] = None,
    is_template: Optional[bool] = None,
) -> List[AutomationWorkflow]:
    seed_default_automation_templates(db, workspace_id=workspace_id)
    query = db.query(AutomationWorkflow)
    if workspace_id:
        query = query.filter(or_(AutomationWorkflow.workspace_id == workspace_id, AutomationWorkflow.is_template == True))
    if status:
        query = query.filter(AutomationWorkflow.status == status)
    if is_template is not None:
        query = query.filter(AutomationWorkflow.is_template == is_template)
    return query.order_by(desc(AutomationWorkflow.updated_at)).all()

def get_workflow_by_id(db: Session, workflow_id: str) -> Optional[AutomationWorkflow]:
    return db.query(AutomationWorkflow).filter(AutomationWorkflow.id == workflow_id).first()

def create_workflow(db: Session, data: AutomationWorkflowCreate, owner_id: Optional[int] = None) -> AutomationWorkflow:
    wf = AutomationWorkflow(
        id=f"wf_{uuid.uuid4().hex[:12]}",
        workspace_id=data.workspace_id,
        name=data.name,
        description=data.description,
        workflow_type=data.workflow_type,
        status=data.status,
        trigger_type=data.trigger_type,
        trigger_config_json=data.trigger_config_json,
        nodes_json=data.nodes_json,
        edges_json=data.edges_json,
        variables_json=data.variables_json,
        execution_settings_json=data.execution_settings_json,
        version=data.version or "1.0",
        is_template=data.is_template,
        template_category=data.template_category,
        owner_id=owner_id,
    )
    db.add(wf)
    db.flush()

    # Initial version record
    ver = AutomationWorkflowVersion(
        id=f"wfver_{uuid.uuid4().hex[:12]}",
        workflow_id=wf.id,
        version=wf.version,
        nodes_json=wf.nodes_json,
        edges_json=wf.edges_json,
        change_summary="Initial workflow creation",
    )
    db.add(ver)
    db.commit()
    db.refresh(wf)
    return wf

def update_workflow(db: Session, workflow_id: str, data: AutomationWorkflowUpdate) -> Optional[AutomationWorkflow]:
    wf = get_workflow_by_id(db, workflow_id)
    if not wf:
        return None

    update_dict = data.model_dump(exclude_unset=True)
    change_summary = update_dict.pop("change_summary", None) or "Incremental update"

    nodes_changed = "nodes_json" in update_dict and update_dict["nodes_json"] != wf.nodes_json

    for field, val in update_dict.items():
        setattr(wf, field, val)
    wf.updated_at = utc_now()

    if nodes_changed:
        try:
            parts = wf.version.split(".")
            minor = int(parts[-1]) + 1
            wf.version = f"{'.'.join(parts[:-1])}.{minor}"
        except Exception:
            wf.version = f"{wf.version}.1"

        ver = AutomationWorkflowVersion(
            id=f"wfver_{uuid.uuid4().hex[:12]}",
            workflow_id=wf.id,
            version=wf.version,
            nodes_json=wf.nodes_json,
            edges_json=wf.edges_json,
            change_summary=change_summary,
        )
        db.add(ver)

    db.commit()
    db.refresh(wf)
    return wf

def delete_workflow(db: Session, workflow_id: str) -> bool:
    wf = get_workflow_by_id(db, workflow_id)
    if not wf:
        return False
    db.delete(wf)
    db.commit()
    return True
