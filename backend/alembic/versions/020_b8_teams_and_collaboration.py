"""B8: Teams, Members, Collaboration, Invitations & Team Management Backend

Revision ID: 020_b8_teams_and_collaboration
Revises: 019_b7_calendar_reminders
Create Date: 2026-11-22 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '020_b8_teams_and_collaboration'
down_revision = '019_b7_calendar_reminders'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 0. Sync missing columns in organizations and organization_members if needed
    if 'organizations' in existing_tables:
        org_cols = [c['name'] for c in inspector.get_columns('organizations')]
        if 'plan' not in org_cols:
            op.add_column('organizations', sa.Column('plan', sa.String(length=32), server_default='starter', nullable=False))
        if 'logo_url' not in org_cols:
            op.add_column('organizations', sa.Column('logo_url', sa.String(length=255), nullable=True))
        if 'is_active' not in org_cols:
            op.add_column('organizations', sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False))

    if 'organization_members' in existing_tables:
        mem_cols = [c['name'] for c in inspector.get_columns('organization_members')]
        if 'title' not in mem_cols:
            op.add_column('organization_members', sa.Column('title', sa.String(length=100), nullable=True))
        if 'is_active' not in mem_cols:
            op.add_column('organization_members', sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False))

    # 1. Create teams table
    if 'teams' not in existing_tables:
        op.create_table(
            'teams',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('slug', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('visibility', sa.String(length=32), server_default='ORGANIZATION', nullable=False),
            sa.Column('status', sa.String(length=32), server_default='active', nullable=False),
            sa.Column('settings_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('avatar_url', sa.String(length=255), nullable=True),
            sa.Column('is_archived', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('archived_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.UniqueConstraint('organization_id', 'slug', name='uq_team_org_slug'),
        )
        op.create_index('ix_teams_org_id', 'teams', ['organization_id'])
        op.create_index('ix_teams_slug', 'teams', ['slug'])
        op.create_index('ix_teams_workspace_id', 'teams', ['workspace_id'])
        op.create_index('ix_teams_owner_id', 'teams', ['owner_id'])
        op.create_index('ix_teams_is_archived', 'teams', ['is_archived'])
        op.create_index('ix_teams_org_status', 'teams', ['organization_id', 'status'])

    # 2. Create team_members table
    if 'team_members' not in existing_tables:
        op.create_table(
            'team_members',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('role', sa.String(length=32), server_default='MEMBER', nullable=False),
            sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
            sa.Column('title', sa.String(length=100), nullable=True),
            sa.Column('joined_at', sa.DateTime(), nullable=False),
            sa.Column('invited_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.UniqueConstraint('team_id', 'user_id', name='uq_team_member'),
        )
        op.create_index('ix_team_members_team_id', 'team_members', ['team_id'])
        op.create_index('ix_team_members_user_id', 'team_members', ['user_id'])
        op.create_index('ix_team_member_lookup', 'team_members', ['team_id', 'user_id'])
        op.create_index('ix_team_member_role', 'team_members', ['team_id', 'role'])

    # 3. Create team_invitations table
    if 'team_invitations' not in existing_tables:
        op.create_table(
            'team_invitations',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('workspace_id', sa.Integer(), sa.ForeignKey('workspaces.id', ondelete='SET NULL'), nullable=True),
            sa.Column('inviter_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('invitee_email', sa.String(length=255), nullable=False),
            sa.Column('invitee_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('role', sa.String(length=32), server_default='MEMBER', nullable=False),
            sa.Column('token_hash', sa.String(length=64), unique=True, nullable=False),
            sa.Column('status', sa.String(length=32), server_default='PENDING', nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('accepted_at', sa.DateTime(), nullable=True),
            sa.Column('revoked_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_team_invitations_team_id', 'team_invitations', ['team_id'])
        op.create_index('ix_team_invitations_email', 'team_invitations', ['invitee_email'])
        op.create_index('ix_team_invitations_token_hash', 'team_invitations', ['token_hash'])
        op.create_index('ix_team_invitations_status', 'team_invitations', ['status'])
        op.create_index('ix_team_invitations_team_status', 'team_invitations', ['team_id', 'status'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'team_invitations' in existing_tables:
        op.drop_table('team_invitations')
    if 'team_members' in existing_tables:
        op.drop_table('team_members')
    if 'teams' in existing_tables:
        op.drop_table('teams')
