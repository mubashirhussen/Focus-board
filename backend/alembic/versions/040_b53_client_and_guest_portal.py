"""B53: Client & Guest Portal, Invitations, Project Access, Deliverables, Approvals, Feedback, Reports, and Portal Settings

Revision ID: 040_b53_client_and_guest_portal
Revises: 039_b52_service_desk_and_sla_management
Create Date: 2026-11-24 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '040_b53_client_and_guest_portal'
down_revision = '039_b52_service_desk_and_sla_management'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. guest_profiles
    if 'guest_profiles' not in existing_tables:
        op.create_table(
            'guest_profiles',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('company_name', sa.String(120), nullable=True),
            sa.Column('phone', sa.String(50), nullable=True),
            sa.Column('title', sa.String(100), nullable=True),
            sa.Column('guest_type', sa.String(32), server_default='CLIENT', nullable=False),
            sa.Column('status', sa.String(32), server_default='ACTIVE', nullable=False),
            sa.Column('invited_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('last_access_at', sa.DateTime(), nullable=True),
            sa.Column('settings_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_guest_profile_org_user', 'guest_profiles', ['organization_id', 'user_id'])

    # 2. guest_invitations
    if 'guest_invitations' not in existing_tables:
        op.create_table(
            'guest_invitations',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('invited_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('guest_email', sa.String(255), nullable=False, index=True),
            sa.Column('guest_name', sa.String(100), nullable=False),
            sa.Column('company_name', sa.String(120), nullable=True),
            sa.Column('token_hash', sa.String(128), nullable=False, unique=True, index=True),
            sa.Column('status', sa.String(32), server_default='PENDING', nullable=False, index=True),
            sa.Column('role', sa.String(32), server_default='CLIENT_VIEWER', nullable=False),
            sa.Column('permissions_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('project_ids_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('accepted_at', sa.DateTime(), nullable=True),
            sa.Column('revoked_at', sa.DateTime(), nullable=True),
            sa.Column('accepted_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 3. guest_project_access
    if 'guest_project_access' not in existing_tables:
        op.create_table(
            'guest_project_access',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('guest_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('role', sa.String(32), server_default='CLIENT_VIEWER', nullable=False),
            sa.Column('permissions_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('granted_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint('guest_user_id', 'project_id', name='uq_guest_project_access_user_proj'),
        )

    # 4. client_project_visibility
    if 'client_project_visibility' not in existing_tables:
        op.create_table(
            'client_project_visibility',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('is_shared', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('show_description', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('show_progress', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('progress_mode', sa.String(32), server_default='AUTOMATIC', nullable=False),
            sa.Column('manual_progress_percent', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('show_milestones', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('show_tasks', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('show_deliverables', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('show_documents', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('allow_comments', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('allow_feedback', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('allow_uploads', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('allow_approvals', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('custom_banner_message', sa.Text(), nullable=True),
            sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 5. client_shared_tasks
    if 'client_shared_tasks' not in existing_tables:
        op.create_table(
            'client_shared_tasks',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('task_id', sa.String(64), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('client_title', sa.String(255), nullable=True),
            sa.Column('client_description', sa.Text(), nullable=True),
            sa.Column('client_status', sa.String(32), server_default='IN_PROGRESS', nullable=False),
            sa.Column('client_priority', sa.String(32), server_default='MEDIUM', nullable=False),
            sa.Column('due_date', sa.DateTime(), nullable=True),
            sa.Column('is_visible', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('allow_client_comments', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 6. client_deliverables
    if 'client_deliverables' not in existing_tables:
        op.create_table(
            'client_deliverables',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('task_id', sa.String(64), sa.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('file_name', sa.String(255), nullable=True),
            sa.Column('file_url', sa.String(500), nullable=True),
            sa.Column('file_size', sa.Integer(), server_default='0', nullable=False),
            sa.Column('file_type', sa.String(64), nullable=True),
            sa.Column('version_number', sa.Integer(), server_default='1', nullable=False),
            sa.Column('status', sa.String(32), server_default='SUBMITTED', nullable=False, index=True),
            sa.Column('submitted_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('submitted_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('reviewed_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('review_comments', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 7. client_deliverable_versions
    if 'client_deliverable_versions' not in existing_tables:
        op.create_table(
            'client_deliverable_versions',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('deliverable_id', sa.Integer(), sa.ForeignKey('client_deliverables.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('version_number', sa.Integer(), nullable=False),
            sa.Column('file_name', sa.String(255), nullable=True),
            sa.Column('file_url', sa.String(500), nullable=True),
            sa.Column('file_size', sa.Integer(), server_default='0', nullable=False),
            sa.Column('changelog', sa.Text(), nullable=True),
            sa.Column('submitted_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 8. client_feedbacks
    if 'client_feedbacks' not in existing_tables:
        op.create_table(
            'client_feedbacks',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('guest_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('category', sa.String(32), server_default='GENERAL', nullable=False),
            sa.Column('status', sa.String(32), server_default='NEW', nullable=False, index=True),
            sa.Column('response_text', sa.Text(), nullable=True),
            sa.Column('responded_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('responded_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 9. client_comments
    if 'client_comments' not in existing_tables:
        op.create_table(
            'client_comments',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('task_id', sa.String(64), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('deliverable_id', sa.Integer(), sa.ForeignKey('client_deliverables.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('feedback_id', sa.Integer(), sa.ForeignKey('client_feedbacks.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('is_client_visible', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 10. client_document_access
    if 'client_document_access' not in existing_tables:
        op.create_table(
            'client_document_access',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('file_name', sa.String(255), nullable=False),
            sa.Column('file_url', sa.String(500), nullable=False),
            sa.Column('file_size', sa.Integer(), server_default='0', nullable=False),
            sa.Column('file_type', sa.String(64), nullable=True),
            sa.Column('is_downloadable', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('shared_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 11. client_reports
    if 'client_reports' not in existing_tables:
        op.create_table(
            'client_reports',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('status_override', sa.String(32), nullable=True),
            sa.Column('progress_percent', sa.Float(), server_default='0.0', nullable=False),
            sa.Column('milestones_summary_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('tasks_summary_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('deliverables_summary_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('client_action_items_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('is_published', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('published_at', sa.DateTime(), nullable=True),
            sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    # 12. guest_activity_logs
    if 'guest_activity_logs' not in existing_tables:
        op.create_table(
            'guest_activity_logs',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('guest_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('action', sa.String(64), nullable=False, index=True),
            sa.Column('resource_type', sa.String(32), nullable=True),
            sa.Column('resource_id', sa.String(64), nullable=True),
            sa.Column('details_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, index=True),
        )

    # 13. client_portal_settings
    if 'client_portal_settings' not in existing_tables:
        op.create_table(
            'client_portal_settings',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
            sa.Column('is_portal_enabled', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('allow_guest_invitations', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('default_role', sa.String(32), server_default='CLIENT_VIEWER', nullable=False),
            sa.Column('default_token_expiration_days', sa.Integer(), server_default='7', nullable=False),
            sa.Column('allow_guest_comments', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('allow_guest_uploads', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('require_approval_reason', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('custom_portal_title', sa.String(100), server_default='Client Collaboration Portal', nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )


def downgrade() -> None:
    op.drop_table('client_portal_settings')
    op.drop_table('guest_activity_logs')
    op.drop_table('client_reports')
    op.drop_table('client_document_access')
    op.drop_table('client_comments')
    op.drop_table('client_feedbacks')
    op.drop_table('client_deliverable_versions')
    op.drop_table('client_deliverables')
    op.drop_table('client_shared_tasks')
    op.drop_table('client_project_visibility')
    op.drop_table('guest_project_access')
    op.drop_table('guest_invitations')
    op.drop_table('guest_profiles')
