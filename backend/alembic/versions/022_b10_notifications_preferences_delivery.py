"""B10: Notifications, Notification Preferences, Delivery Channels & Notification Management Backend

Revision ID: 022_b10_notifications_preferences_delivery
Revises: 021_b9_comments_mentions_activity_audit
Create Date: 2026-11-22 22:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '022_b10_notifications_preferences_delivery'
down_revision = '021_b9_comments_mentions_activity_audit'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create notification_deliveries table if not exists
    if 'notification_deliveries' not in existing_tables:
        op.create_table(
            'notification_deliveries',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('notification_id', sa.Integer(), sa.ForeignKey('notifications.id', ondelete='CASCADE'), nullable=False),
            sa.Column('recipient_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('channel', sa.String(length=32), nullable=False),
            sa.Column('status', sa.String(length=32), server_default='PENDING', nullable=False),
            sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('last_attempt_at', sa.DateTime(), nullable=True),
            sa.Column('delivered_at', sa.DateTime(), nullable=True),
            sa.Column('failed_at', sa.DateTime(), nullable=True),
            sa.Column('error_details', sa.Text(), nullable=True),
            sa.Column('idempotency_key', sa.String(length=128), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_notif_deliv_nid', 'notification_deliveries', ['notification_id'])
        op.create_index('ix_notif_deliv_user', 'notification_deliveries', ['recipient_user_id'])
        op.create_index('ix_notif_deliv_idemp', 'notification_deliveries', ['idempotency_key'])

    # 2. Add columns to notifications table
    if 'notifications' in existing_tables:
        existing_cols = [c['name'] for c in inspector.get_columns('notifications')]
        with op.batch_alter_table('notifications') as batch_op:
            if 'organization_id' not in existing_cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in existing_cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            if 'category' not in existing_cols:
                batch_op.add_column(sa.Column('category', sa.String(length=32), server_default='TASK', nullable=False))
            if 'actor_id' not in existing_cols:
                batch_op.add_column(sa.Column('actor_id', sa.Integer(), nullable=True))
            if 'entity_type' not in existing_cols:
                batch_op.add_column(sa.Column('entity_type', sa.String(length=64), nullable=True))
            if 'entity_id' not in existing_cols:
                batch_op.add_column(sa.Column('entity_id', sa.String(length=64), nullable=True))
            if 'project_id' not in existing_cols:
                batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=True))
            if 'team_id' not in existing_cols:
                batch_op.add_column(sa.Column('team_id', sa.Integer(), nullable=True))
            if 'comment_id' not in existing_cols:
                batch_op.add_column(sa.Column('comment_id', sa.Integer(), nullable=True))
            if 'invitation_id' not in existing_cols:
                batch_op.add_column(sa.Column('invitation_id', sa.Integer(), nullable=True))
            if 'priority' not in existing_cols:
                batch_op.add_column(sa.Column('priority', sa.String(length=32), server_default='NORMAL', nullable=False))
            if 'is_archived' not in existing_cols:
                batch_op.add_column(sa.Column('is_archived', sa.Boolean(), server_default='0', nullable=False))
            if 'archived_at' not in existing_cols:
                batch_op.add_column(sa.Column('archived_at', sa.DateTime(), nullable=True))
            if 'metadata_json' not in existing_cols:
                batch_op.add_column(sa.Column('metadata_json', sa.Text(), nullable=True))

    # 3. Add columns to notification_preferences table
    if 'notification_preferences' in existing_tables:
        existing_pref_cols = [c['name'] for c in inspector.get_columns('notification_preferences')]
        with op.batch_alter_table('notification_preferences') as batch_op:
            if 'enable_push' not in existing_pref_cols:
                batch_op.add_column(sa.Column('enable_push', sa.Boolean(), server_default='1', nullable=False))
            if 'enable_task_assigned' not in existing_pref_cols:
                batch_op.add_column(sa.Column('enable_task_assigned', sa.Boolean(), server_default='1', nullable=False))
            if 'enable_comments' not in existing_pref_cols:
                batch_op.add_column(sa.Column('enable_comments', sa.Boolean(), server_default='1', nullable=False))
            if 'enable_mentions' not in existing_pref_cols:
                batch_op.add_column(sa.Column('enable_mentions', sa.Boolean(), server_default='1', nullable=False))
            if 'enable_project_updates' not in existing_pref_cols:
                batch_op.add_column(sa.Column('enable_project_updates', sa.Boolean(), server_default='1', nullable=False))
            if 'enable_team_updates' not in existing_pref_cols:
                batch_op.add_column(sa.Column('enable_team_updates', sa.Boolean(), server_default='1', nullable=False))
            if 'enable_invitations' not in existing_pref_cols:
                batch_op.add_column(sa.Column('enable_invitations', sa.Boolean(), server_default='1', nullable=False))
            if 'category_overrides_json' not in existing_pref_cols:
                batch_op.add_column(sa.Column('category_overrides_json', sa.Text(), nullable=True))
            if 'created_at' not in existing_pref_cols:
                batch_op.add_column(sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))
            if 'updated_at' not in existing_pref_cols:
                batch_op.add_column(sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))

def downgrade() -> None:
    pass
