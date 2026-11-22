import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.models.ai_agent import AIAgent, AIAgentExecution, AIAgentExecutionStep, AIPersistentPreference
from app.models.task import Task
from app.models.collaboration import Project
from app.ai_agent.tools import TOOL_REGISTRY

def construct_agent_plan(
    db: Session,
    agent: AIAgent,
    user_id: int,
    workspace_id: Optional[int],
    prompt: str,
    user_pref: Optional[AIPersistentPreference] = None,
) -> List[Dict[str, Any]]:
    """
    Generate a structured, deterministic multi-step plan based on the user's prompt,
    the selected agent's role, and the user's active workload.
    """
    prompt_lower = prompt.lower()
    allowed_tools = json.loads(agent.tools_json or "[]")
    plan_steps: List[Dict[str, Any]] = []

    # 1. TASK PLANNING AGENT
    if agent.agent_type == "TASK_PLANNER":
        # Always inspect backlog first
        plan_steps.append({
            "step_index": 0,
            "description": "Analyze active task backlog and priority distribution",
            "tool_name": "list_tasks",
            "arguments": {"status": "todo", "limit": 20},
            "requires_approval": False,
        })

        if "tomorrow" in prompt_lower or "today" in prompt_lower or "schedule" in prompt_lower or "daily" in prompt_lower:
            hours = user_pref.preferred_work_hours if user_pref else 6
            plan_steps.append({
                "step_index": 1,
                "description": f"Generate prioritized {hours}-hour daily plan with inter-task buffers",
                "tool_name": "create_daily_plan",
                "arguments": {"available_hours": hours},
                "requires_approval": False,
            })

        if "create" in prompt_lower or "add task" in prompt_lower:
            # Extract suggested title
            match = re.search(r'(?:create|add)(?:\s+a|\s+new)?\s+task\s+(?:named|called|to|for)?\s*[\'":]?(.*?)[\'":]?$', prompt, re.IGNORECASE)
            task_title = match.group(1).strip() if match and match.group(1) else "Review high priority deliverables"
            plan_steps.append({
                "step_index": len(plan_steps),
                "description": f"Create scheduled task: {task_title[:40]}",
                "tool_name": "create_task",
                "arguments": {"title": task_title, "priority": "high"},
                "requires_approval": False,
            })

        if "delete" in prompt_lower or "remove" in prompt_lower:
            # Find a target task or place a delete placeholder
            target = db.query(Task).filter(Task.user_id == user_id).first()
            target_id = target.id if target else "task-placeholder"
            plan_steps.append({
                "step_index": len(plan_steps),
                "description": f"Delete target task ({target_id})",
                "tool_name": "delete_task",
                "arguments": {"task_id": target_id},
                "requires_approval": True,  # Sensitive!
            })

    # 2. TASK BREAKDOWN AGENT
    elif agent.agent_type == "TASK_BREAKDOWN":
        # Get target task or list tasks
        plan_steps.append({
            "step_index": 0,
            "description": "Retrieve target assignment details and dependencies",
            "tool_name": "list_tasks",
            "arguments": {"limit": 5},
            "requires_approval": False,
        })
        # Add subtasks
        plan_steps.append({
            "step_index": 1,
            "description": "Deconstruct step 1: Environment & Requirements Setup",
            "tool_name": "create_task",
            "arguments": {"title": f"Phase 1: Setup & Prerequisites ({prompt[:30]})", "priority": "medium"},
            "requires_approval": False,
        })
        plan_steps.append({
            "step_index": 2,
            "description": "Deconstruct step 2: Core Execution & Implementation",
            "tool_name": "create_task",
            "arguments": {"title": f"Phase 2: Core Implementation ({prompt[:30]})", "priority": "high"},
            "requires_approval": False,
        })
        plan_steps.append({
            "step_index": 3,
            "description": "Deconstruct step 3: Verification & Launch",
            "tool_name": "create_task",
            "arguments": {"title": f"Phase 3: Verification & Review ({prompt[:30]})", "priority": "low"},
            "requires_approval": False,
        })

    # 3. PROJECT PLANNER AGENT
    elif agent.agent_type == "PROJECT_PLANNER":
        project_name = "New Initiative Project"
        m = re.search(r'(?:project|for)\s+(?:named|called)?\s*[\'":]?(.*?)[\'":]?$', prompt, re.IGNORECASE)
        if m and m.group(1):
            project_name = m.group(1).strip()[:50]

        plan_steps.append({
            "step_index": 0,
            "description": f"Create project container: {project_name}",
            "tool_name": "create_project",
            "arguments": {"name": project_name, "description": f"AI-architected project for: {prompt}"},
            "requires_approval": False,
        })
        plan_steps.append({
            "step_index": 1,
            "description": "Create milestone task: Architecture & Scope Definition",
            "tool_name": "create_task",
            "arguments": {"title": f"Define scope for {project_name}", "priority": "high"},
            "requires_approval": False,
        })
        plan_steps.append({
            "step_index": 2,
            "description": "Create milestone task: Core Sprint Deliverables",
            "tool_name": "create_task",
            "arguments": {"title": f"Execute core deliverables for {project_name}", "priority": "medium"},
            "requires_approval": False,
        })

    # 4. PRODUCTIVITY INSIGHTS AGENT
    elif agent.agent_type == "PRODUCTIVITY_INSIGHTS":
        plan_steps.append({
            "step_index": 0,
            "description": "Query completion velocity, overdue counts, and focus metrics",
            "tool_name": "get_productivity_analytics",
            "arguments": {},
            "requires_approval": False,
        })
        plan_steps.append({
            "step_index": 1,
            "description": "Evaluate active task backlog distribution",
            "tool_name": "list_tasks",
            "arguments": {"limit": 10},
            "requires_approval": False,
        })

    # 5. CUSTOMER SUPPORT AGENT
    elif agent.agent_type == "CUSTOMER_SUPPORT":
        plan_steps.append({
            "step_index": 0,
            "description": "Search official documentation and knowledge base",
            "tool_name": "search_knowledge_base",
            "arguments": {"query": prompt[:50]},
            "requires_approval": False,
        })
        if "ticket" in prompt_lower or "support" in prompt_lower or "escalate" in prompt_lower or "help" in prompt_lower:
            plan_steps.append({
                "step_index": 1,
                "description": "Open customer support ticket with SLA guarantee",
                "tool_name": "create_support_ticket",
                "arguments": {
                    "title": f"Assistance Request: {prompt[:40]}",
                    "description": prompt,
                    "priority": "HIGH" if "urgent" in prompt_lower else "NORMAL",
                },
                "requires_approval": False,
            })

    # 6. WORKFLOW AUTOMATION AGENT
    else:
        plan_steps.append({
            "step_index": 0,
            "description": "Inspect workspace state for automation context",
            "tool_name": "list_tasks",
            "arguments": {"limit": 10},
            "requires_approval": False,
        })
        plan_steps.append({
            "step_index": 1,
            "description": f"Execute workflow action for: {prompt[:40]}",
            "tool_name": "create_task",
            "arguments": {"title": f"Automated Task: {prompt[:40]}", "priority": "medium"},
            "requires_approval": False,
        })

    # Filter steps to only allowed tools for this agent
    filtered_steps = []
    for s in plan_steps:
        if s["tool_name"] in allowed_tools:
            s["step_index"] = len(filtered_steps)
            filtered_steps.append(s)

    return filtered_steps
