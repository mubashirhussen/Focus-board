"""B6: Complete Boards, Lists, Views, Filters, Columns, Grouping & Saved Views

Revision ID: 018_b6_boards_and_views
Revises: 017_b5_tasks_management
Create Date: 2026-11-22 21:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '018_b6_boards_and_views'
down_revision = '017_b5_tasks_management'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create boards table
    if 'boards' not in existing_tables:
        op.create_table(
            'boards',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
            sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('name', sa.String(150), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('board_type', sa.String(50), server_default='kanban', nullable=False),
            sa.Column('visibility', sa.String(50), server_default='workspace', nullable=False),
            sa.Column('settings_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('is_default', sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column('is_archived', sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column('archived_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_boards_organization_id', 'boards', ['organization_id'])
        op.create_index('ix_boards_workspace_id', 'boards', ['workspace_id'])
        op.create_index('ix_boards_project_id', 'boards', ['project_id'])
        op.create_index('ix_boards_owner_id', 'boards', ['owner_id'])
        op.create_index('ix_boards_name', 'boards', ['name'])
        op.create_index('ix_boards_is_archived', 'boards', ['is_archived'])
        op.create_index('ix_boards_ws_archived', 'boards', ['workspace_id', 'is_archived'])
        op.create_index('ix_boards_proj_archived', 'boards', ['project_id', 'is_archived'])

    # 2. Create board_columns table
    if 'board_columns' not in existing_tables:
        op.create_table(
            'board_columns',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('board_id', sa.String(64), sa.ForeignKey('boards.id', ondelete='CASCADE'), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('status_value', sa.String(50), nullable=False),
            sa.Column('position', sa.Integer(), server_default='0', nullable=False),
            sa.Column('color', sa.String(32), server_default='#6366f1', nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('wip_limit', sa.Integer(), nullable=True),
            sa.Column('is_visible', sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_board_columns_board_id', 'board_columns', ['board_id'])
        op.create_index('ix_board_columns_status_value', 'board_columns', ['status_value'])
        op.create_index('ix_board_cols_order', 'board_columns', ['board_id', 'position'])

    # 3. Create board_views table
    if 'board_views' not in existing_tables:
        op.create_table(
            'board_views',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
            sa.Column('board_id', sa.String(64), sa.ForeignKey('boards.id', ondelete='CASCADE'), nullable=True),
            sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('name', sa.String(150), nullable=False),
            sa.Column('view_type', sa.String(50), server_default='kanban', nullable=False),
            sa.Column('visibility', sa.String(50), server_default='workspace', nullable=False),
            sa.Column('filters_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('sort_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('group_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('column_config_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('is_default', sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_board_views_workspace_id', 'board_views', ['workspace_id'])
        op.create_index('ix_board_views_project_id', 'board_views', ['project_id'])
        op.create_index('ix_board_views_board_id', 'board_views', ['board_id'])
        op.create_index('ix_board_views_owner_id', 'board_views', ['owner_id'])
        op.create_index('ix_board_views_ws_type', 'board_views', ['workspace_id', 'view_type'])
        op.create_index('ix_board_views_proj_type', 'board_views', ['project_id', 'view_type'])

    # 4. Create saved_filters table
    if 'saved_filters' not in existing_tables:
        op.create_table(
            'saved_filters',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('name', sa.String(150), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('filter_type', sa.String(50), server_default='task', nullable=False),
            sa.Column('query_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('is_shared', sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_saved_filters_user_id', 'saved_filters', ['user_id'])
        op.create_index('ix_saved_filters_workspace_id', 'saved_filters', ['workspace_id'])
        op.create_index('ix_saved_filters_project_id', 'saved_filters', ['project_id'])

def downgrade() -> None:
    pass
