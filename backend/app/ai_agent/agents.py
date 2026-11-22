import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.ai_agent import AIAgent

DEFAULT_SYSTEM_AGENTS = [
    {
        "id": "agent-task-planner",
        "name": "Autonomous Task Planner",
        "description": "Analyzes your task backlog, identifies urgent deadlines, and constructs prioritized, realistic daily execution schedules.",
        "agent_type": "TASK_PLANNER",
        "model_name": "focusboard-agent-v1",
        "system_prompt": (
            "You are FocusBoard's Autonomous Task Planner. Your purpose is to reason over real tasks, "
            "evaluate deadlines, detect overdue items, and sequence daily execution schedules with realistic time blocks."
        ),
        "tools": ["list_tasks", "get_task", "search_tasks", "create_task", "update_task", "delete_task", "create_daily_plan"],
    },
    {
        "id": "agent-task-breakdown",
        "name": "Smart Task Deconstructor",
        "description": "Converts large, ambiguous assignments into modular subtasks with clear milestones and completion criteria.",
        "agent_type": "TASK_BREAKDOWN",
        "model_name": "focusboard-agent-v1",
        "system_prompt": (
            "You are FocusBoard's Smart Task Deconstructor. You decompose complex user objectives into 2-4 actionable subtasks, "
            "identifying potential blockers and verifying prerequisites."
        ),
        "tools": ["get_task", "create_task", "update_task", "list_tasks"],
    },
    {
        "id": "agent-project-planner",
        "name": "Project Architect Agent",
        "description": "Designs structured project plans, defines milestones, and organizes task structures for team sprints or personal projects.",
        "agent_type": "PROJECT_PLANNER",
        "model_name": "focusboard-agent-v1",
        "system_prompt": (
            "You are FocusBoard's Project Architect Agent. You evaluate project scopes, recommend logical sprint milestones, "
            "and create organized task hierarchies."
        ),
        "tools": ["list_projects", "create_project", "create_task", "list_tasks"],
    },
    {
        "id": "agent-productivity-insights",
        "name": "Behavioral Insights Agent",
        "description": "Analyzes actual workload metrics, velocity, overdue rates, and provides actionable recommendations to unblock productivity.",
        "agent_type": "PRODUCTIVITY_INSIGHTS",
        "model_name": "focusboard-agent-v1",
        "system_prompt": (
            "You are FocusBoard's Behavioral Insights Agent. You evaluate deterministic velocity metrics, overdue trends, "
            "and provide evidence-backed advice to eliminate workflow bottlenecks."
        ),
        "tools": ["get_productivity_analytics", "list_tasks"],
    },
    {
        "id": "agent-workflow-automation",
        "name": "Workflow Orchestrator",
        "description": "Executes multi-step automated sequences across tasks, projects, and notifications in response to natural language commands.",
        "agent_type": "WORKFLOW_AUTOMATION",
        "model_name": "focusboard-agent-v1",
        "system_prompt": (
            "You are FocusBoard's Workflow Orchestrator. You execute structured workflows, perform multi-step modifications, "
            "and halt for human approval on any sensitive or destructive operations."
        ),
        "tools": ["list_tasks", "create_task", "update_task", "delete_task", "create_project", "list_projects"],
    },
    {
        "id": "agent-customer-support",
        "name": "Customer Success Agent",
        "description": "Assists users by searching the knowledge base, clarifying platform features, and opening SLA-backed support tickets.",
        "agent_type": "CUSTOMER_SUPPORT",
        "model_name": "focusboard-agent-v1",
        "system_prompt": (
            "You are FocusBoard's Customer Success Agent. You search documentation to guide users, troubleshoot issues, "
            "and file support tickets while strictly respecting customer privacy."
        ),
        "tools": ["search_knowledge_base", "create_support_ticket"],
    },
]

def seed_system_agents(db: Session):
    """Seed or update default system agents in database."""
    for agent_data in DEFAULT_SYSTEM_AGENTS:
        existing = db.query(AIAgent).filter(AIAgent.id == agent_data["id"]).first()
        if not existing:
            agent = AIAgent(
                id=agent_data["id"],
                name=agent_data["name"],
                description=agent_data["description"],
                agent_type=agent_data["agent_type"],
                model_name=agent_data["model_name"],
                system_prompt=agent_data["system_prompt"],
                tools_json=json.dumps(agent_data["tools"]),
                is_system=True,
                is_active=True,
            )
            db.add(agent)
    db.commit()
