import os
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, inspect

def test_alembic_migrations_lifecycle():
    """Verify that Alembic migrations execute cleanly from base to head without errors."""
    test_db_file = "test_migrations_temp.db"
    if os.path.exists(test_db_file):
        os.remove(test_db_file)

    try:
        # Configure Alembic
        alembic_cfg = Config("backend/alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{test_db_file}")
        alembic_cfg.set_main_option("script_location", "backend/alembic")

        # 1. Run migrations upgrade to head
        command.upgrade(alembic_cfg, "head")

        # 2. Inspect resulting schema
        engine = create_engine(f"sqlite:///{test_db_file}")
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Verify key tables across all 5 migrations exist
        expected_tables = [
            "users",
            "tasks",
            "notifications",
            "workspaces",
            "workspace_members",
            "projects",
            "task_comments",
            "activities",
            "audit_logs",
            "plans",
            "subscriptions",
            "external_integrations",
            "push_subscriptions",
            "organization_policies",
            "custom_roles",
            "organization_domains",
            "user_mfa",
            "intelligence_preferences",
            "onboarding_progress",
            "product_analytics_events",
            "customer_feedbacks",
            "support_tickets",
            "support_messages",
            "knowledge_base_categories",
            "knowledge_base_articles",
            "product_roadmap_items",
            "ai_agents",
            "ai_agent_executions",
            "ai_agent_execution_steps",
            "ai_agent_approvals",
            "ai_persistent_preferences",
            "user_regional_settings",
            "project_milestones",
            "project_risks",
            "resource_capacities",
            "analytics_reports",
            "developer_applications",
            "developer_credentials",
            "webhook_subscriptions",
            "webhook_deliveries",
            "api_usage_records",
            "idempotency_records",
            "compliance_controls",
            "compliance_evidences",
            "security_policies",
            "policy_acknowledgments",
            "security_risk_items",
            "security_incidents",
            "security_vendors",
            "privacy_requests",
            "trust_center_documents",
            "financial_transactions",
            "financial_metric_snapshots",
            "cost_records",
            "financial_budgets",
            "financial_forecasts",
            "strategic_plans",
            "strategic_goals",
            "strategic_initiatives",
            "market_intelligences",
            "market_signals",
            "competitors",
            "swot_entries",
            "market_sizings",
            "strategic_opportunities",
            "strategic_scenarios",
            "strategic_decisions",
            "innovation_ideas",
            "innovation_hypotheses",
            "innovation_experiments",
            "innovation_experiment_results",
            "innovation_prototypes",
            "innovation_validations",
            "innovation_portfolios",
            "knowledge_documents",
            "knowledge_document_versions",
            "knowledge_collections",
            "knowledge_entities",
            "knowledge_relationships",
            "organizational_memories",
            "knowledge_gaps",
            "automation_workflows",
            "automation_workflow_versions",
            "automation_executions",
            "automation_execution_logs",
            "automation_approvals",
            "automation_schedules",
            "integration_providers",
            "marketplace_listings",
            "marketplace_installations",
            "oauth_connectors",
        ]

        for table in expected_tables:
            assert table in tables, f"Expected table '{table}' missing after alembic upgrade head"

        # Verify foreign keys and column definitions on tasks
        columns = [col["name"] for col in inspector.get_columns("tasks")]
        assert "id" in columns
        assert "title" in columns
        assert "user_id" in columns
        assert "workspace_id" in columns
        assert "status" in columns

    finally:
        if os.path.exists(test_db_file):
            try:
                os.remove(test_db_file)
            except Exception:
                pass
