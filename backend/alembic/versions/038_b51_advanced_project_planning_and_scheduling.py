"""B51: Advanced Project Planning, Scheduling, Gantt, Critical Path, Baselines, Budgets & Simulations

Revision ID: 038_b51_advanced_project_planning_and_scheduling
Revises: 037_b50_goals_okrs_and_milestones
Create Date: 2026-11-24 19:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '038_b51_advanced_project_planning_and_scheduling'
down_revision = '037_b50_goals_okrs_and_milestones'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Extend task_dependencies with lag & audit columns if missing
    if 'task_dependencies' in existing_tables:
        existing_cols = [c['name'] for c in inspector.get_columns('task_dependencies')]
        with op.batch_alter_table('task_dependencies') as batch_op:
            if 'lag_duration' not in existing_cols:
                batch_op.add_column(sa.Column('lag_duration', sa.Float(), server_default='0.0', nullable=False))
            if 'lag_unit' not in existing_cols:
                batch_op.add_column(sa.Column('lag_unit', sa.String(16), server_default='DAYS', nullable=False))
            if 'created_by' not in existing_cols:
                batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))

    # 2. project_schedules
    if 'project_schedules' not in existing_tables:
        op.create_table(
            'project_schedules',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), unique=True, nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('planning_mode', sa.String(32), server_default='CPM_DRIVEN', nullable=False),
            sa.Column('working_days_json', sa.Text(), server_default='["MON","TUE","WED","THU","FRI"]', nullable=False),
            sa.Column('working_hours_per_day', sa.Float(), server_default='8.0', nullable=False),
            sa.Column('calendar_holidays_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('critical_path_duration_days', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('critical_tasks_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('schedule_health', sa.String(32), server_default='ON_TRACK', nullable=False, index=True),
            sa.Column('schedule_health_reasons_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('planned_start_date', sa.DateTime(), nullable=True),
            sa.Column('planned_end_date', sa.DateTime(), nullable=True),
            sa.Column('calculated_earliest_finish', sa.DateTime(), nullable=True),
            sa.Column('forecast_completion_date', sa.DateTime(), nullable=True),
            sa.Column('schedule_variance_days', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('active_baseline_id', sa.Integer(), nullable=True),
            sa.Column('auto_recalculate', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )

    # 3. project_baselines
    if 'project_baselines' not in existing_tables:
        op.create_table(
            'project_baselines',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('name', sa.String(120), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('version', sa.Integer(), server_default='1', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('is_archived', sa.Boolean(), server_default='0', nullable=False, index=True),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('planned_start', sa.DateTime(), nullable=True),
            sa.Column('planned_end', sa.DateTime(), nullable=True),
            sa.Column('total_duration_days', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('total_estimated_effort_hours', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('total_budget', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('currency', sa.String(8), server_default='USD', nullable=False),
            sa.Column('metadata_json', sa.Text(), server_default='{}', nullable=False),
        )

    # 4. baseline_task_snapshots
    if 'baseline_task_snapshots' not in existing_tables:
        op.create_table(
            'baseline_task_snapshots',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('baseline_id', sa.Integer(), sa.ForeignKey('project_baselines.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('task_id', sa.String(64), nullable=False, index=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('start_date', sa.String(50), nullable=True),
            sa.Column('due_date', sa.String(50), nullable=True),
            sa.Column('duration_days', sa.Float(), server_default='1.0', nullable=False),
            sa.Column('progress_percent', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('estimated_effort_hours', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('status', sa.String(50), server_default='Todo', nullable=False),
            sa.Column('priority', sa.String(50), server_default='Medium', nullable=False),
            sa.Column('assignee_id', sa.Integer(), nullable=True),
        )

    # 5. baseline_milestone_snapshots
    if 'baseline_milestone_snapshots' not in existing_tables:
        op.create_table(
            'baseline_milestone_snapshots',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('baseline_id', sa.Integer(), sa.ForeignKey('project_baselines.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('milestone_id', sa.String(64), nullable=False, index=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('due_date', sa.String(50), nullable=True),
            sa.Column('status', sa.String(50), server_default='PENDING', nullable=False),
        )

    # 6. project_budgets
    if 'project_budgets' not in existing_tables:
        op.create_table(
            'project_budgets',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), unique=True, nullable=False, index=True),
            sa.Column('currency', sa.String(8), server_default='USD', nullable=False),
            sa.Column('total_budget', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('committed_cost', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('actual_cost', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('forecast_cost', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('is_approved', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('approved_at', sa.DateTime(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )

    # 7. project_budget_categories
    if 'project_budget_categories' not in existing_tables:
        op.create_table(
            'project_budget_categories',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('budget_id', sa.Integer(), sa.ForeignKey('project_budgets.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('category_name', sa.String(64), nullable=False),
            sa.Column('budgeted_amount', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('committed_amount', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('actual_amount', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('forecast_amount', sa.Float(), server_default='0.0', nullable=False),
        )

    # 8. project_cost_records
    if 'project_cost_records' not in existing_tables:
        op.create_table(
            'project_cost_records',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('budget_id', sa.Integer(), sa.ForeignKey('project_budgets.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('category_id', sa.Integer(), sa.ForeignKey('project_budget_categories.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('description', sa.String(255), nullable=False),
            sa.Column('amount', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('currency', sa.String(8), server_default='USD', nullable=False),
            sa.Column('record_type', sa.String(32), server_default='ACTUAL', nullable=False),
            sa.Column('date_incurred', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 9. project_schedule_scenarios
    if 'project_schedule_scenarios' not in existing_tables:
        op.create_table(
            'project_schedule_scenarios',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('name', sa.String(120), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(32), server_default='DRAFT', nullable=False),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('applied_at', sa.DateTime(), nullable=True),
            sa.Column('assumptions_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('outcomes_json', sa.Text(), server_default='{}', nullable=False),
        )

    # 10. scenario_task_changes
    if 'scenario_task_changes' not in existing_tables:
        op.create_table(
            'scenario_task_changes',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('scenario_id', sa.Integer(), sa.ForeignKey('project_schedule_scenarios.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('task_id', sa.String(64), nullable=False, index=True),
            sa.Column('proposed_start_date', sa.String(50), nullable=True),
            sa.Column('proposed_due_date', sa.String(50), nullable=True),
            sa.Column('proposed_duration_days', sa.Float(), nullable=True),
            sa.Column('proposed_priority', sa.String(50), nullable=True),
            sa.Column('proposed_assignee_id', sa.Integer(), nullable=True),
        )

    # 11. project_schedule_forecasts
    if 'project_schedule_forecasts' not in existing_tables:
        op.create_table(
            'project_schedule_forecasts',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('planned_completion_date', sa.DateTime(), nullable=True),
            sa.Column('forecast_completion_date', sa.DateTime(), nullable=True),
            sa.Column('schedule_variance_days', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('critical_path_duration_days', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('health_status', sa.String(32), server_default='ON_TRACK', nullable=False),
            sa.Column('confidence_score', sa.Float(), server_default='0.85', nullable=False),
            sa.Column('calculation_factors_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('calculated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

def downgrade() -> None:
    op.drop_table('project_schedule_forecasts')
    op.drop_table('scenario_task_changes')
    op.drop_table('project_schedule_scenarios')
    op.drop_table('project_cost_records')
    op.drop_table('project_budget_categories')
    op.drop_table('project_budgets')
    op.drop_table('baseline_milestone_snapshots')
    op.drop_table('baseline_task_snapshots')
    op.drop_table('project_baselines')
    op.drop_table('project_schedules')
