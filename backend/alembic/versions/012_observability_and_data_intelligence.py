"""Add platform observability, incidents, SLOs, analytics datasets, pipelines, and data quality tables

Revision ID: 012_observability_and_data_intelligence
Revises: 011_automation_and_integration_platform
Create Date: 2026-11-22 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '012_observability_and_data_intelligence'
down_revision = '011_automation_and_integration_platform'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # --- PHASE 41: PLATFORM OBSERVABILITY & INCIDENT MANAGEMENT ---
    # 1. Service Registry
    op.create_table(
        'service_registry',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('category', sa.String(length=60), nullable=False),
        sa.Column('health_endpoint', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='OPERATIONAL', nullable=False),
        sa.Column('response_time_ms', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('last_checked_at', sa.DateTime(), nullable=False),
        sa.Column('dependencies_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('failure_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_service_registry_status', 'service_registry', ['status'])
    op.create_index('ix_service_registry_category', 'service_registry', ['category'])

    # 2. Platform Alert Rules
    op.create_table(
        'platform_alert_rules',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('condition_operator', sa.String(length=20), server_default='GREATER_THAN', nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(length=20), server_default='WARNING', nullable=False),
        sa.Column('evaluation_interval_seconds', sa.Integer(), server_default='60', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 3. Platform Alerts
    op.create_table(
        'platform_alerts',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('rule_id', sa.String(length=64), sa.ForeignKey('platform_alert_rules.id', ondelete='CASCADE'), nullable=True),
        sa.Column('severity', sa.String(length=20), server_default='WARNING', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('summary', sa.String(length=255), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('related_service_id', sa.String(length=64), sa.ForeignKey('service_registry.id', ondelete='SET NULL'), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_platform_alerts_status', 'platform_alerts', ['status'])
    op.create_index('ix_platform_alerts_severity', 'platform_alerts', ['severity'])

    # 4. Platform Incidents
    op.create_table(
        'platform_incidents',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=10), server_default='SEV3', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='DETECTED', nullable=False),
        sa.Column('affected_services_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('lead_operator_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('mitigation_summary', sa.Text(), nullable=True),
        sa.Column('resolution_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_platform_incidents_status', 'platform_incidents', ['status'])
    op.create_index('ix_platform_incidents_severity', 'platform_incidents', ['severity'])

    # 5. Incident Timeline Entries
    op.create_table(
        'incident_timeline_entries',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('incident_id', sa.String(length=64), sa.ForeignKey('platform_incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entry_type', sa.String(length=50), server_default='UPDATE', nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('actor_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_incident_timeline_incident', 'incident_timeline_entries', ['incident_id'])

    # 6. Incident Action Items
    op.create_table(
        'incident_action_items',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('incident_id', sa.String(length=64), sa.ForeignKey('platform_incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action_description', sa.Text(), nullable=False),
        sa.Column('assignee_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_completed', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_incident_action_items_incident', 'incident_action_items', ['incident_id'])

    # 7. Incident Post-Mortem
    op.create_table(
        'incident_post_mortems',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('incident_id', sa.String(length=64), sa.ForeignKey('platform_incidents.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('impact_summary', sa.Text(), nullable=False),
        sa.Column('root_cause_analysis', sa.Text(), nullable=False),
        sa.Column('lessons_learned', sa.Text(), nullable=False),
        sa.Column('preventative_measures', sa.Text(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=False),
    )

    # 8. SLO Definitions
    op.create_table(
        'slo_definitions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('service_id', sa.String(length=64), sa.ForeignKey('service_registry.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('target_percentage', sa.Float(), server_default='99.9', nullable=False),
        sa.Column('measurement_window_days', sa.Integer(), server_default='30', nullable=False),
        sa.Column('current_sli_percentage', sa.Float(), server_default='99.95', nullable=False),
        sa.Column('error_budget_remaining_percent', sa.Float(), server_default='95.0', nullable=False),
        sa.Column('burn_rate', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 9. Maintenance Windows
    op.create_table(
        'platform_maintenance_windows',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='SCHEDULED', nullable=False),
        sa.Column('scheduled_start', sa.DateTime(), nullable=False),
        sa.Column('scheduled_end', sa.DateTime(), nullable=False),
        sa.Column('affected_services_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # --- PHASE 42: DATA INTELLIGENCE & ENTERPRISE ANALYTICS ---
    # 10. Analytics Datasets
    op.create_table(
        'analytics_datasets',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('slug', sa.String(length=120), unique=True, nullable=False),
        sa.Column('category', sa.String(length=60), server_default='PRODUCTIVITY', nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('data_source', sa.String(length=100), nullable=False),
        sa.Column('freshness_status', sa.String(length=20), server_default='FRESH', nullable=False),
        sa.Column('record_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('schema_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('last_refreshed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_analytics_datasets_category', 'analytics_datasets', ['category'])
    op.create_index('ix_analytics_datasets_freshness', 'analytics_datasets', ['freshness_status'])

    # 11. Analytics Metric Definitions
    op.create_table(
        'analytics_metric_definitions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('identifier', sa.String(length=100), unique=True, nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('category', sa.String(length=60), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('calculation_method', sa.String(length=100), nullable=False),
        sa.Column('unit', sa.String(length=30), server_default='count', nullable=False),
        sa.Column('aggregation_method', sa.String(length=30), server_default='SUM', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
    )
    op.create_index('ix_analytics_metric_definitions_cat', 'analytics_metric_definitions', ['category'])

    # 12. Analytics Data Pipelines
    op.create_table(
        'analytics_data_pipelines',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('source_dataset_slug', sa.String(length=120), nullable=False),
        sa.Column('target_model', sa.String(length=100), nullable=False),
        sa.Column('schedule_cron', sa.String(length=50), server_default='0 * * * *', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_run_status', sa.String(length=20), server_default='SUCCESS', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 13. Pipeline Executions
    op.create_table(
        'analytics_pipeline_executions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('pipeline_id', sa.String(length=64), sa.ForeignKey('analytics_data_pipelines.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='COMPLETED', nullable=False),
        sa.Column('records_processed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('duration_ms', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_analytics_pipeline_executions_pipe', 'analytics_pipeline_executions', ['pipeline_id'])

    # 14. Analytics Dashboards
    op.create_table(
        'analytics_dashboards',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('visibility', sa.String(length=20), server_default='WORKSPACE', nullable=False),
        sa.Column('layout_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 15. Analytics Widgets
    op.create_table(
        'analytics_widgets',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('dashboard_id', sa.String(length=64), sa.ForeignKey('analytics_dashboards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('widget_type', sa.String(length=30), server_default='KPI', nullable=False),
        sa.Column('metric_identifier', sa.String(length=100), nullable=False),
        sa.Column('config_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('position_order', sa.Integer(), server_default='0', nullable=False),
    )

    # 16. Analytics Custom Reports
    op.create_table(
        'analytics_custom_reports',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=60), server_default='PRODUCTIVITY', nullable=False),
        sa.Column('query_config_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('format', sa.String(length=20), server_default='CSV', nullable=False),
        sa.Column('schedule_cron', sa.String(length=50), nullable=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
    )

    # 17. Data Quality Rules
    op.create_table(
        'data_quality_rules',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('dataset_slug', sa.String(length=120), nullable=False),
        sa.Column('rule_name', sa.String(length=150), nullable=False),
        sa.Column('rule_type', sa.String(length=40), server_default='COMPLETENESS', nullable=False),
        sa.Column('severity', sa.String(length=20), server_default='WARNING', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='PASS', nullable=False),
        sa.Column('condition_expr', sa.String(length=255), nullable=False),
        sa.Column('last_evaluated_at', sa.DateTime(), nullable=False),
    )

    # 18. Data Quality Issues
    op.create_table(
        'data_quality_issues',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('rule_id', sa.String(length=64), sa.ForeignKey('data_quality_rules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dataset_slug', sa.String(length=120), nullable=False),
        sa.Column('issue_summary', sa.String(length=255), nullable=False),
        sa.Column('severity', sa.String(length=20), server_default='WARNING', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='OPEN', nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
    )

def downgrade() -> None:
    op.drop_table('data_quality_issues')
    op.drop_table('data_quality_rules')
    op.drop_table('analytics_custom_reports')
    op.drop_table('analytics_widgets')
    op.drop_table('analytics_dashboards')
    op.drop_table('analytics_pipeline_executions')
    op.drop_table('analytics_data_pipelines')
    op.drop_table('analytics_metric_definitions')
    op.drop_table('analytics_datasets')
    op.drop_table('platform_maintenance_windows')
    op.drop_table('slo_definitions')
    op.drop_table('incident_post_mortems')
    op.drop_table('incident_action_items')
    op.drop_table('incident_timeline_entries')
    op.drop_table('platform_incidents')
    op.drop_table('platform_alerts')
    op.drop_table('platform_alert_rules')
    op.drop_table('service_registry')
