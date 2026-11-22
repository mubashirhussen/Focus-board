"""B4: Complete Projects Backend, Project Lifecycle, CRUD, Memberships, Templates & Dependencies

Revision ID: 016_b4_projects_management
Revises: 015_b2_b3_auth_and_organizations
Create Date: 2026-11-22 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '016_b4_projects_management'
down_revision = '015_b2_b3_auth_and_organizations'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Update projects table using SQLite batch mode
    proj_cols = [c['name'] for c in inspector.get_columns('projects')]
    with op.batch_alter_table('projects') as batch_op:
        if 'organization_id' not in proj_cols:
            batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            batch_op.create_index('ix_projects_organization_id', ['organization_id'])
        if 'owner_id' not in proj_cols:
            batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=True))
            batch_op.create_index('ix_projects_owner_id', ['owner_id'])
        if 'slug' not in proj_cols:
            batch_op.add_column(sa.Column('slug', sa.String(120), nullable=True))
            batch_op.create_index('ix_projects_slug', ['slug'])
        if 'health' not in proj_cols:
            batch_op.add_column(sa.Column('health', sa.String(32), server_default='ON_TRACK', nullable=False))
        if 'priority' not in proj_cols:
            batch_op.add_column(sa.Column('priority', sa.String(32), server_default='MEDIUM', nullable=False))
        if 'visibility' not in proj_cols:
            batch_op.add_column(sa.Column('visibility', sa.String(32), server_default='WORKSPACE', nullable=False))
        if 'start_date' not in proj_cols:
            batch_op.add_column(sa.Column('start_date', sa.DateTime(), nullable=True))
        if 'due_date' not in proj_cols:
            batch_op.add_column(sa.Column('due_date', sa.DateTime(), nullable=True))
        if 'color' not in proj_cols:
            batch_op.add_column(sa.Column('color', sa.String(32), server_default='#4F46E5', nullable=True))
        if 'icon' not in proj_cols:
            batch_op.add_column(sa.Column('icon', sa.String(64), server_default='folder', nullable=True))
        if 'category' not in proj_cols:
            batch_op.add_column(sa.Column('category', sa.String(64), server_default='General', nullable=False))
        if 'tags_json' not in proj_cols:
            batch_op.add_column(sa.Column('tags_json', sa.Text(), server_default='[]', nullable=False))
        if 'settings_json' not in proj_cols:
            batch_op.add_column(sa.Column('settings_json', sa.Text(), server_default='{}', nullable=False))
        if 'is_archived' not in proj_cols:
            batch_op.add_column(sa.Column('is_archived', sa.Boolean(), server_default='0', nullable=False))
        if 'archived_at' not in proj_cols:
            batch_op.add_column(sa.Column('archived_at', sa.DateTime(), nullable=True))
        if 'is_deleted' not in proj_cols:
            batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False))
        if 'deleted_at' not in proj_cols:
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # 2. Project Members table
    if 'project_members' not in existing_tables:
        op.create_table(
            'project_members',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('role', sa.String(32), server_default='PROJECT_MEMBER', nullable=False),
            sa.Column('status', sa.String(32), server_default='ACTIVE', nullable=False),
            sa.Column('joined_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_project_member_unique', 'project_members', ['project_id', 'user_id'], unique=True)

    # 3. Project Templates table
    if 'project_templates' not in existing_tables:
        op.create_table(
            'project_templates',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True, index=True),
            sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('category', sa.String(64), server_default='General', nullable=False),
            sa.Column('default_settings_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('default_tasks_json', sa.Text(), server_default='[]', nullable=False),
            sa.Column('visibility', sa.String(32), server_default='ORGANIZATION', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    # 4. Project Dependencies table
    if 'project_dependencies' not in existing_tables:
        op.create_table(
            'project_dependencies',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('depends_on_project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('dependency_type', sa.String(32), server_default='FINISH_TO_START', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_project_dep_unique', 'project_dependencies', ['project_id', 'depends_on_project_id'], unique=True)

def downgrade() -> None:
    pass
