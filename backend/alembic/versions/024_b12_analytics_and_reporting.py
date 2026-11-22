"""B12: Analytics, Productivity Reports, KPIs, Dashboards & Performance Metrics Backend

Revision ID: 024_b12_analytics_and_reporting
Revises: 023_b11_search_history_saved_searches_indexes
Create Date: 2026-11-22 22:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '024_b12_analytics_and_reporting'
down_revision = '023_b11_search_history_saved_searches_indexes'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    def safe_create_index(index_name: str, table_name: str, columns: list):
        if table_name in existing_tables:
            existing_indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
            if index_name not in existing_indexes:
                try:
                    op.create_index(index_name, table_name, columns)
                except Exception:
                    pass

    safe_create_index('ix_tasks_ws_status', 'tasks', ['workspace_id', 'status'])
    safe_create_index('ix_tasks_proj_status', 'tasks', ['project_id', 'status'])
    safe_create_index('ix_tasks_due_date_status', 'tasks', ['due_date', 'status'])
    safe_create_index('ix_activities_actor_created', 'activities', ['actor_id', 'created_at'])
    safe_create_index('ix_projects_ws_health', 'projects', ['workspace_id', 'health'])

def downgrade() -> None:
    pass
