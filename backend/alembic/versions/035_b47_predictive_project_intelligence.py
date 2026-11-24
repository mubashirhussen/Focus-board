"""B47: Predictive Project Intelligence (Health Snapshots, Task Risks, Forecasts, Workload, Recommendations, History, Settings)

Revision ID: 035_b47_predictive_project_intelligence
Revises: 034_auth_otp_and_verification
Create Date: 2026-11-24 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '035_b47_predictive_project_intelligence'
down_revision = '034_auth_otp_and_verification'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. project_health_snapshots
    if 'project_health_snapshots' not in existing_tables:
        op.create_table(
            'project_health_snapshots',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('health_score', sa.Float(), nullable=False, server_default='100.0'),
            sa.Column('health_status', sa.String(32), nullable=False, server_default='HEALTHY', index=True),
            sa.Column('risk_factors_json', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('positive_indicators_json', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('recommended_actions_json', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.9'),
            sa.Column('metrics_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('calculated_at', sa.DateTime(), nullable=False, index=True),
        )

    # 2. task_risk_predictions
    if 'task_risk_predictions' not in existing_tables:
        op.create_table(
            'task_risk_predictions',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('task_id', sa.String(64), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('risk_level', sa.String(32), nullable=False, server_default='LOW', index=True),
            sa.Column('risk_score', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('primary_factors_json', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('supporting_evidence_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('suggested_action', sa.Text(), nullable=True),
            sa.Column('confidence', sa.Float(), nullable=False, server_default='0.85'),
            sa.Column('calculated_at', sa.DateTime(), nullable=False, index=True),
        )

    # 3. deadline_forecasts
    if 'deadline_forecasts' not in existing_tables:
        op.create_table(
            'deadline_forecasts',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('planned_completion_date', sa.DateTime(), nullable=True),
            sa.Column('predicted_completion_date', sa.DateTime(), nullable=False),
            sa.Column('estimated_delay_days', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('confidence_interval_low', sa.DateTime(), nullable=True),
            sa.Column('confidence_interval_high', sa.DateTime(), nullable=True),
            sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.85'),
            sa.Column('delay_factors_json', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('critical_path_tasks_json', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('recommended_actions_json', sa.Text(), nullable=False, server_default='[]'),
            sa.Column('calculated_at', sa.DateTime(), nullable=False, index=True),
        )

    # 4. workload_snapshots
    if 'workload_snapshots' not in existing_tables:
        op.create_table(
            'workload_snapshots',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('assigned_tasks_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('open_tasks_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('overdue_tasks_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('estimated_minutes_total', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('capacity_utilization_rate', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('workload_tier', sa.String(32), nullable=False, server_default='BALANCED', index=True),
            sa.Column('calculated_at', sa.DateTime(), nullable=False, index=True),
        )

    # 5. ai_project_recommendations
    if 'ai_project_recommendations' not in existing_tables:
        op.create_table(
            'ai_project_recommendations',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('recommendation_key', sa.String(64), nullable=False, unique=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('task_id', sa.String(64), sa.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('category', sa.String(64), nullable=False, server_default='RISK_MITIGATION', index=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('supporting_evidence_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('expected_impact', sa.String(255), nullable=False),
            sa.Column('priority', sa.String(32), nullable=False, server_default='MEDIUM', index=True),
            sa.Column('status', sa.String(32), nullable=False, server_default='PENDING', index=True),
            sa.Column('reviewed_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        )

    # 6. prediction_history
    if 'prediction_history' not in existing_tables:
        op.create_table(
            'prediction_history',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('entity_type', sa.String(32), nullable=False, index=True),
            sa.Column('entity_id', sa.String(64), nullable=False, index=True),
            sa.Column('project_id', sa.Integer(), nullable=True, index=True),
            sa.Column('organization_id', sa.Integer(), nullable=True, index=True),
            sa.Column('prediction_type', sa.String(64), nullable=False, index=True),
            sa.Column('original_prediction_json', sa.Text(), nullable=False),
            sa.Column('updated_prediction_json', sa.Text(), nullable=True),
            sa.Column('actual_outcome_json', sa.Text(), nullable=True),
            sa.Column('accuracy_score', sa.Float(), nullable=True),
            sa.Column('error_days', sa.Float(), nullable=True),
            sa.Column('prediction_method', sa.String(64), nullable=False, server_default='STATISTICAL'),
            sa.Column('model_version', sa.String(32), nullable=False, server_default='v1.0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
        )

    # 7. intelligence_settings
    if 'intelligence_settings' not in existing_tables:
        op.create_table(
            'intelligence_settings',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, unique=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('high_risk_threshold', sa.Float(), nullable=False, server_default='70.0'),
            sa.Column('overdue_task_weight', sa.Float(), nullable=False, server_default='0.35'),
            sa.Column('dependency_blocker_weight', sa.Float(), nullable=False, server_default='0.25'),
            sa.Column('workload_overload_hours', sa.Float(), nullable=False, server_default='40.0'),
            sa.Column('alert_cooldown_hours', sa.Integer(), nullable=False, server_default='24'),
            sa.Column('auto_alerts_enabled', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('forecast_confidence_level', sa.Float(), nullable=False, server_default='0.85'),
            sa.Column('settings_json', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    for table in [
        'intelligence_settings',
        'prediction_history',
        'ai_project_recommendations',
        'workload_snapshots',
        'deadline_forecasts',
        'task_risk_predictions',
        'project_health_snapshots',
    ]:
        if table in existing_tables:
            op.drop_table(table)
