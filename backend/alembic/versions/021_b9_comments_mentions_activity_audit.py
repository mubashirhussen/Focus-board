"""B9: Comments, Mentions, Activity Feeds, Discussion Threads, Collaboration History & Audit Logs Backend

Revision ID: 021_b9_comments_mentions_activity_audit
Revises: 020_b8_teams_and_collaboration
Create Date: 2026-11-22 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '021_b9_comments_mentions_activity_audit'
down_revision = '020_b8_teams_and_collaboration'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create comments table
    if 'comments' not in existing_tables:
        op.create_table(
            'comments',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True),
            sa.Column('entity_type', sa.String(length=32), server_default='TASK', nullable=False),
            sa.Column('entity_id', sa.String(length=64), nullable=False),
            sa.Column('task_id', sa.String(length=64), nullable=True),
            sa.Column('project_id', sa.Integer(), nullable=True),
            sa.Column('board_id', sa.Integer(), nullable=True),
            sa.Column('team_id', sa.Integer(), nullable=True),
            sa.Column('parent_comment_id', sa.Integer(), sa.ForeignKey('comments.id', ondelete='CASCADE'), nullable=True),
            sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('content_format', sa.String(length=32), server_default='markdown', nullable=False),
            sa.Column('is_edited', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('metadata_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_comments_organization_id', 'comments', ['organization_id'])
        op.create_index('ix_comments_workspace_id', 'comments', ['workspace_id'])
        op.create_index('ix_comments_author_id', 'comments', ['author_id'])
        op.create_index('ix_comments_parent_id', 'comments', ['parent_comment_id'])
        op.create_index('ix_comments_entity', 'comments', ['entity_type', 'entity_id'])
        op.create_index('ix_comments_task_created', 'comments', ['task_id', 'created_at'])

    # 2. Create comment_mentions table
    if 'comment_mentions' not in existing_tables:
        op.create_table(
            'comment_mentions',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('comment_id', sa.Integer(), sa.ForeignKey('comments.id', ondelete='CASCADE'), nullable=False),
            sa.Column('mentioned_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('mentioned_by_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('entity_type', sa.String(length=32), nullable=False),
            sa.Column('entity_id', sa.String(length=64), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.UniqueConstraint('comment_id', 'mentioned_user_id', name='uq_comment_mention'),
        )
        op.create_index('ix_comment_mentions_comment_id', 'comment_mentions', ['comment_id'])
        op.create_index('ix_comment_mentions_user_id', 'comment_mentions', ['mentioned_user_id'])
        op.create_index('ix_comment_mentions_user_org', 'comment_mentions', ['mentioned_user_id', 'organization_id'])

    # 3. Create comment_reactions table
    if 'comment_reactions' not in existing_tables:
        op.create_table(
            'comment_reactions',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('comment_id', sa.Integer(), sa.ForeignKey('comments.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('reaction_type', sa.String(length=32), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.UniqueConstraint('comment_id', 'user_id', 'reaction_type', name='uq_comment_reaction'),
        )
        op.create_index('ix_comment_reactions_comment_id', 'comment_reactions', ['comment_id'])
        op.create_index('ix_comment_reactions_user_id', 'comment_reactions', ['user_id'])
        op.create_index('ix_comment_reactions_lookup', 'comment_reactions', ['comment_id', 'user_id'])

    # 4. Enhance activities table if columns missing
    if 'activities' in existing_tables:
        act_cols = [c['name'] for c in inspector.get_columns('activities')]
        with op.batch_alter_table('activities') as batch_op:
            batch_op.alter_column('workspace_id', existing_type=sa.Integer(), nullable=True)
            if 'organization_id' not in act_cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'entity_type' not in act_cols:
                batch_op.add_column(sa.Column('entity_type', sa.String(length=32), server_default='TASK', nullable=True))
            if 'entity_id' not in act_cols:
                batch_op.add_column(sa.Column('entity_id', sa.String(length=64), nullable=True))
            if 'parent_entity_id' not in act_cols:
                batch_op.add_column(sa.Column('parent_entity_id', sa.String(length=64), nullable=True))
            if 'target_user_id' not in act_cols:
                batch_op.add_column(sa.Column('target_user_id', sa.Integer(), nullable=True))
            if 'metadata_json' not in act_cols:
                batch_op.add_column(sa.Column('metadata_json', sa.Text(), nullable=True))

    # 5. Enhance audit_logs table if columns missing
    if 'audit_logs' in existing_tables:
        audit_cols = [c['name'] for c in inspector.get_columns('audit_logs')]
        with op.batch_alter_table('audit_logs') as batch_op:
            if 'organization_id' not in audit_cols:
                batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            if 'workspace_id' not in audit_cols:
                batch_op.add_column(sa.Column('workspace_id', sa.Integer(), nullable=True))
            if 'before_state_json' not in audit_cols:
                batch_op.add_column(sa.Column('before_state_json', sa.Text(), nullable=True))
            if 'after_state_json' not in audit_cols:
                batch_op.add_column(sa.Column('after_state_json', sa.Text(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'comment_reactions' in existing_tables:
        op.drop_table('comment_reactions')
    if 'comment_mentions' in existing_tables:
        op.drop_table('comment_mentions')
    if 'comments' in existing_tables:
        op.drop_table('comments')
