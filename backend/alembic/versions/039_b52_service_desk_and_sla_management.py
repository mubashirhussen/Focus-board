"""B52: Service Desk & SLA Management, Tickets, Categories, Policies, Breaches, Escalations, Assignments, and Conversations

Revision ID: 039_b52_service_desk_and_sla_management
Revises: 038_b51_advanced_project_planning_and_scheduling
Create Date: 2026-11-24 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '039_b52_service_desk_and_sla_management'
down_revision = '038_b51_advanced_project_planning_and_scheduling'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. service_desk_categories
    if 'service_desk_categories' not in existing_tables:
        op.create_table(
            'service_desk_categories',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('default_priority', sa.String(20), server_default='MEDIUM', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint('organization_id', 'name', name='uq_service_desk_category_org_name'),
        )

    # 2. service_desk_sla_policies
    if 'service_desk_sla_policies' not in existing_tables:
        op.create_table(
            'service_desk_sla_policies',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('version', sa.Integer(), server_default='1', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('is_default', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('first_response_target_minutes', sa.Integer(), server_default='60', nullable=False),
            sa.Column('resolution_target_minutes', sa.Integer(), server_default='480', nullable=False),
            sa.Column('business_hours_start', sa.String(10), server_default='09:00', nullable=False),
            sa.Column('business_hours_end', sa.String(10), server_default='17:00', nullable=False),
            sa.Column('work_days', sa.String(50), server_default='MON,TUE,WED,THU,FRI', nullable=False),
            sa.Column('timezone', sa.String(50), server_default='UTC', nullable=False),
            sa.Column('applies_to_categories_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('applies_to_priorities_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('allow_pause_on_waiting', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('at_risk_threshold_percentage', sa.Float(), server_default='80.0', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )

    # 3. service_desk_tickets
    if 'service_desk_tickets' not in existing_tables:
        op.create_table(
            'service_desk_tickets',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('ticket_number', sa.String(32), unique=True, index=True, nullable=False),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('subject', sa.String(255), nullable=False, index=True),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('requester_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('assigned_agent_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('assigned_team_id', sa.Integer(), sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('category_id', sa.Integer(), sa.ForeignKey('service_desk_categories.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('category_name', sa.String(64), server_default='Technical Support', nullable=False, index=True),
            sa.Column('subcategory', sa.String(64), nullable=True),
            sa.Column('priority', sa.String(20), server_default='MEDIUM', nullable=False, index=True),
            sa.Column('status', sa.String(32), server_default='NEW', nullable=False, index=True),
            sa.Column('source', sa.String(32), server_default='PORTAL', nullable=False),
            sa.Column('sla_policy_id', sa.Integer(), sa.ForeignKey('service_desk_sla_policies.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('sla_policy_version', sa.Integer(), server_default='1', nullable=False),
            sa.Column('first_response_due_at', sa.DateTime(), nullable=True),
            sa.Column('resolution_due_at', sa.DateTime(), nullable=True),
            sa.Column('first_response_at', sa.DateTime(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('closed_at', sa.DateTime(), nullable=True),
            sa.Column('reopened_at', sa.DateTime(), nullable=True),
            sa.Column('sla_response_status', sa.String(20), server_default='ON_TRACK', nullable=False),
            sa.Column('sla_resolution_status', sa.String(20), server_default='ON_TRACK', nullable=False),
            sa.Column('sla_paused_at', sa.DateTime(), nullable=True),
            sa.Column('total_sla_pause_minutes', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('resolution_notes', sa.Text(), nullable=True),
            sa.Column('related_project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('related_task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('tags_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, index=True),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )

    # 4. service_desk_comments
    if 'service_desk_comments' not in existing_tables:
        op.create_table(
            'service_desk_comments',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('service_desk_tickets.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('is_internal_note', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )

    # 5. service_desk_attachments
    if 'service_desk_attachments' not in existing_tables:
        op.create_table(
            'service_desk_attachments',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('service_desk_tickets.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('uploader_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('filename', sa.String(255), nullable=False),
            sa.Column('file_url', sa.String(512), nullable=False),
            sa.Column('file_size', sa.Integer(), server_default='0', nullable=False),
            sa.Column('content_type', sa.String(100), server_default='application/octet-stream', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 6. service_desk_assignment_history
    if 'service_desk_assignment_history' not in existing_tables:
        op.create_table(
            'service_desk_assignment_history',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('service_desk_tickets.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('assigned_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('previous_agent_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('new_agent_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('previous_team_id', sa.Integer(), sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True),
            sa.Column('new_team_id', sa.Integer(), sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 7. service_desk_activity_logs
    if 'service_desk_activity_logs' not in existing_tables:
        op.create_table(
            'service_desk_activity_logs',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('service_desk_tickets.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('action', sa.String(64), nullable=False),
            sa.Column('previous_value', sa.String(255), nullable=True),
            sa.Column('new_value', sa.String(255), nullable=True),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 8. service_desk_escalation_rules
    if 'service_desk_escalation_rules' not in existing_tables:
        op.create_table(
            'service_desk_escalation_rules',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('trigger_type', sa.String(32), server_default='SLA_BREACH', nullable=False),
            sa.Column('threshold_minutes', sa.Integer(), server_default='60', nullable=False),
            sa.Column('target_action', sa.String(32), server_default='NOTIFY_ADMIN', nullable=False),
            sa.Column('target_agent_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('target_team_id', sa.Integer(), sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True),
            sa.Column('target_priority', sa.String(20), nullable=True),
            sa.Column('is_enabled', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 9. service_desk_escalation_records
    if 'service_desk_escalation_records' not in existing_tables:
        op.create_table(
            'service_desk_escalation_records',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('service_desk_tickets.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('rule_id', sa.Integer(), sa.ForeignKey('service_desk_escalation_rules.id', ondelete='SET NULL'), nullable=True),
            sa.Column('triggered_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('action_taken', sa.String(64), nullable=False),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 10. service_desk_sla_breaches
    if 'service_desk_sla_breaches' not in existing_tables:
        op.create_table(
            'service_desk_sla_breaches',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('service_desk_tickets.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('policy_id', sa.Integer(), sa.ForeignKey('service_desk_sla_policies.id', ondelete='SET NULL'), nullable=True),
            sa.Column('breach_type', sa.String(32), nullable=False),
            sa.Column('target_deadline', sa.DateTime(), nullable=False),
            sa.Column('breached_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('minutes_overdue', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('is_acknowledged', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

def downgrade() -> None:
    tables = [
        'service_desk_sla_breaches',
        'service_desk_escalation_records',
        'service_desk_escalation_rules',
        'service_desk_activity_logs',
        'service_desk_assignment_history',
        'service_desk_attachments',
        'service_desk_comments',
        'service_desk_tickets',
        'service_desk_sla_policies',
        'service_desk_categories',
    ]
    for tbl in tables:
        op.drop_table(tbl)
