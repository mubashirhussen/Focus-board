"""B11: Global Search, Advanced Filtering, Sorting, Pagination & Search Intelligence Backend

Revision ID: 023_b11_search_history_saved_searches_indexes
Revises: 022_b10_notifications_preferences_delivery
Create Date: 2026-11-22 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '023_b11_search_history_saved_searches_indexes'
down_revision = '022_b10_notifications_preferences_delivery'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create search_histories table
    if 'search_histories' not in existing_tables:
        op.create_table(
            'search_histories',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('query', sa.String(length=255), nullable=False),
            sa.Column('normalized_query', sa.String(length=255), nullable=False),
            sa.Column('entity_type', sa.String(length=32), server_default='ALL', nullable=False),
            sa.Column('filters_json', sa.Text(), nullable=True),
            sa.Column('result_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('last_searched_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_search_histories_user_id', 'search_histories', ['user_id'])
        op.create_index('ix_search_histories_normalized_query', 'search_histories', ['normalized_query'])
        op.create_index('ix_search_histories_user_last_searched', 'search_histories', ['user_id', 'last_searched_at'])

    # 2. Create saved_searches table
    if 'saved_searches' not in existing_tables:
        op.create_table(
            'saved_searches',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
            sa.Column('name', sa.String(length=128), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('entity_type', sa.String(length=32), server_default='TASK', nullable=False),
            sa.Column('query', sa.String(length=255), nullable=True),
            sa.Column('filter_definition_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('sorting_config_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('is_shared', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_saved_searches_user_id', 'saved_searches', ['user_id'])
        op.create_index('ix_saved_searches_organization_id', 'saved_searches', ['organization_id'])
        op.create_index('ix_saved_searches_user_entity', 'saved_searches', ['user_id', 'entity_type'])
        op.create_index('ix_saved_searches_org_shared', 'saved_searches', ['organization_id', 'is_shared'])

    # 3. Add search optimization indexes if not already present
    def safe_create_index(index_name: str, table_name: str, columns: list):
        if table_name in existing_tables:
            existing_indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
            if index_name not in existing_indexes:
                try:
                    op.create_index(index_name, table_name, columns)
                except Exception:
                    pass

    safe_create_index('ix_tasks_title_search', 'tasks', ['title'])
    safe_create_index('ix_projects_name_search', 'projects', ['name'])
    safe_create_index('ix_teams_name_search', 'teams', ['name'])
    safe_create_index('ix_workspaces_name_search', 'workspaces', ['name'])
    safe_create_index('ix_boards_name_search', 'boards', ['name'])
    safe_create_index('ix_comments_content_search', 'comments', ['content'])

def downgrade() -> None:
    pass
