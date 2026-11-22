"""B5: Complete Task Management Backend Implementation, Subtasks, Assignment, Priorities, Status, Dependencies & Lifecycle

Revision ID: 017_b5_tasks_management
Revises: 016_b4_projects_management
Create Date: 2026-11-22 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '017_b5_tasks_management'
down_revision = '016_b4_projects_management'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Update tasks table using SQLite batch mode
    task_cols = [c['name'] for c in inspector.get_columns('tasks')]
    with op.batch_alter_table('tasks') as batch_op:
        if 'organization_id' not in task_cols:
            batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            batch_op.create_index('ix_tasks_organization_id', ['organization_id'])
        if 'parent_task_id' not in task_cols:
            batch_op.add_column(sa.Column('parent_task_id', sa.String(64), nullable=True))
            batch_op.create_index('ix_tasks_parent_task_id', ['parent_task_id'])
        if 'sort_order' not in task_cols:
            batch_op.add_column(sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False))
            batch_op.create_index('ix_tasks_sort_order', ['sort_order'])
        if 'actual_minutes' not in task_cols:
            batch_op.add_column(sa.Column('actual_minutes', sa.Integer(), server_default='0', nullable=False))
        if 'progress_percent' not in task_cols:
            batch_op.add_column(sa.Column('progress_percent', sa.Float(), server_default='0.0', nullable=False))
        if 'labels_json' not in task_cols:
            batch_op.add_column(sa.Column('labels_json', sa.Text(), server_default='[]', nullable=False))
        if 'is_archived' not in task_cols:
            batch_op.add_column(sa.Column('is_archived', sa.Boolean(), server_default=sa.false(), nullable=False))
            batch_op.create_index('ix_tasks_is_archived', ['is_archived'])
        if 'archived_at' not in task_cols:
            batch_op.add_column(sa.Column('archived_at', sa.DateTime(), nullable=True))
        if 'is_deleted' not in task_cols:
            batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), server_default=sa.false(), nullable=False))
            batch_op.create_index('ix_tasks_is_deleted', ['is_deleted'])
        if 'deleted_at' not in task_cols:
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # 2. Create task_dependencies table if not exists
    if 'task_dependencies' not in existing_tables:
        op.create_table(
            'task_dependencies',
            sa.Column('id', sa.String(64), primary_key=True),
            sa.Column('task_id', sa.String(64), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
            sa.Column('depends_on_task_id', sa.String(64), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
            sa.Column('dependency_type', sa.String(32), server_default='FINISH_TO_START', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint('task_id', 'depends_on_task_id', name='uq_task_dependency_pair')
        )
        op.create_index('ix_task_dependencies_task_id', 'task_dependencies', ['task_id'])
        op.create_index('ix_task_dependencies_depends_on', 'task_dependencies', ['depends_on_task_id'])
        op.create_index('ix_task_dep_pair', 'task_dependencies', ['task_id', 'depends_on_task_id'])

def downgrade() -> None:
    pass
