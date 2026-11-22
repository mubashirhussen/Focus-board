import time
import json
import re
from typing import List, Dict, Any, Optional
from app.ai.providers.base import BaseLLMProvider, LLMResponse

class MockProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "focusboard-mock-v1"):
        self.model_name = model_name

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        start_time = time.time()
        combined_text = (prompt or "") + " " + " ".join(m.get("content", "") for m in (messages or []))
        lower = combined_text.lower()

        # Check if structured JSON response is requested
        if json_mode:
            content = self._generate_json_response(lower, prompt)
        else:
            content = self._generate_text_response(lower, prompt)

        latency_ms = int((time.time() - start_time) * 1000)
        in_tokens = max(1, len(combined_text) // 4)
        out_tokens = max(1, len(content) // 4)

        return LLMResponse(
            content=content,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            total_tokens=in_tokens + out_tokens,
            provider="mock",
            model=self.model_name,
            latency_ms=latency_ms,
        )

    def _generate_json_response(self, lower: str, raw_prompt: str) -> str:
        if "decompose" in lower or "subtask" in lower or "break down" in lower:
            data = {
                "subtasks": [
                    {
                        "title": "Analyze requirements and prepare environment",
                        "description": "Review current implementation, specifications, and dependencies.",
                        "estimated_minutes": 30,
                        "priority": "Medium",
                        "order": 1,
                        "acceptance_criteria": "Scope and setup validated."
                    },
                    {
                        "title": "Implement core deliverables and functionality",
                        "description": "Construct primary module components adhering to standards.",
                        "estimated_minutes": 90,
                        "priority": "High",
                        "order": 2,
                        "acceptance_criteria": "Core implementation working and integrated."
                    },
                    {
                        "title": "Verify quality, write automated tests and documentation",
                        "description": "Execute regression testing, ensure complete coverage.",
                        "estimated_minutes": 45,
                        "priority": "Medium",
                        "order": 3,
                        "acceptance_criteria": "All tests pass cleanly and documentation updated."
                    }
                ],
                "summary": "Task broken down into 3 structured execution steps."
            }
            return json.dumps(data)

        if "plan" in lower and "task" in lower:
            data = {
                "steps": [
                    {
                        "order": 1,
                        "action": "Review prerequisites, architectural specifications, and gather dependencies",
                        "estimated_minutes": 30,
                        "checkpoint": "Prerequisites verified"
                    },
                    {
                        "order": 2,
                        "action": "Execute core deliverable implementation and configurations",
                        "estimated_minutes": 90,
                        "checkpoint": "Core functionality operational"
                    },
                    {
                        "order": 3,
                        "action": "Run automated test suites and verify edge case handling",
                        "estimated_minutes": 45,
                        "checkpoint": "All verification checks passing"
                    }
                ],
                "estimated_total_minutes": 165,
                "potential_blockers": ["Resource constraints", "Dependency review delays"],
                "recommended_focus": "Maintain dedicated uninterrupted focus on execution."
            }
            return json.dumps(data)

        if "plan" in lower and "project" in lower:
            data = {
                "objectives": [
                    "Deliver core milestones on schedule with zero critical blockers",
                    "Maintain high quality with automated regression tests",
                    "Ensure seamless stakeholder communication and visibility"
                ],
                "phases": [
                    {
                        "name": "Phase 1: Architecture & Design",
                        "suggested_duration_days": 5,
                        "suggested_tasks": ["Draft system architecture", "Define API schema", "Review dependencies"],
                        "risk_factors": ["Ambiguous requirements", "Resource bottlenecks"]
                    },
                    {
                        "name": "Phase 2: Implementation & Integration",
                        "suggested_duration_days": 10,
                        "suggested_tasks": ["Develop backend services", "Integrate client APIs", "Database migrations"],
                        "risk_factors": ["Scope creep", "Integration delays"]
                    },
                    {
                        "name": "Phase 3: Verification & Launch",
                        "suggested_duration_days": 5,
                        "suggested_tasks": ["Run end-to-end test suite", "Conduct security audit", "Deploy to staging"],
                        "risk_factors": ["Unresolved bugs"]
                    }
                ],
                "estimated_total_days": 20
            }
            return json.dumps(data)

        if "risk" in lower:
            data = {
                "risk_level": "Moderate",
                "risk_score": 6.5,
                "summary": "Project is progressing steadily with minor overdue items that should be rebalanced.",
                "identified_risks": [
                    {
                        "severity": "High",
                        "category": "Schedule Adherence",
                        "description": "Overdue assignments may impact downstream delivery timeline.",
                        "mitigation_strategy": "Reschedule low-priority tasks and focus team bandwidth on blocking items."
                    },
                    {
                        "severity": "Medium",
                        "category": "Capacity",
                        "description": "Workload concentration on primary contributors creates single-point dependency.",
                        "mitigation_strategy": "Delegate non-critical tasks across available members."
                    }
                ],
                "recommended_actions": [
                    "Prioritize resolving overdue tasks today",
                    "Conduct weekly milestone check-in with assignees"
                ]
            }
            return json.dumps(data)

        if "create" in lower or "assist" in lower:
            data = {
                "title": "Implement authentication and session handling",
                "description": "Establish robust user authentication, JWT session verification, and token refresh mechanisms.",
                "category": "Engineering",
                "priority": "High",
                "estimated_minutes": 120,
                "suggested_deadline_days": 3,
                "acceptance_criteria": [
                    "User registration and login return valid tokens",
                    "Protected endpoints reject unauthenticated requests"
                ],
                "labels": ["backend", "security", "auth"]
            }
            return json.dumps(data)

        # Default fallback JSON
        return json.dumps({"result": "Success", "summary": "Operation analyzed successfully."})

    def _generate_text_response(self, lower: str, raw_prompt: str) -> str:
        if "today" in lower or "work on" in lower or "priorit" in lower:
            return (
                "Based on your current FocusBoard workload, here is your recommended focus plan:\n"
                "1. Address any critical overdue items to protect your delivery schedule.\n"
                "2. Tackle high-priority assignments during your morning deep work block.\n"
                "3. Reserve remaining time for review and administrative follow-ups."
            )
        if "overdue" in lower:
            return "Reviewing your active assignments, overdue items have been prioritized for immediate resolution or rescheduling."
        if "summar" in lower:
            return "Summary of accessible records: Work is actively progressing across assigned projects with tracked completion velocity."
        
        return "I am your FocusBoard AI Assistant. I can help you plan your schedule, decompose tasks, analyze project risk, and prioritize work based on real application data."
