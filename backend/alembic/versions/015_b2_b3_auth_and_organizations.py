"""B2 and B3: Authentication sessions, tokens, organizations and multi-tenant scoping

Revision ID: 015_b2_b3_auth_and_organizations
Revises: 014_product_lifecycle_hardening
Create Date: 2026-11-22 19:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '015_b2_b3_auth_and_organizations'
down_revision = '014_product_lifecycle_hardening'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Update users table with B2 profile and status fields
    user_cols = [c['name'] for c in inspector.get_columns('users')]
    with op.batch_alter_table('users') as batch_op:
        if 'display_name' not in user_cols:
            batch_op.add_column(sa.Column('display_name', sa.String(100), nullable=True))
        if 'status' not in user_cols:
            batch_op.add_column(sa.Column('status', sa.String(32), server_default='active', nullable=False))
        if 'is_verified' not in user_cols:
            batch_op.add_column(sa.Column('is_verified', sa.Boolean(), server_default='1', nullable=False))
        if 'timezone' not in user_cols:
            batch_op.add_column(sa.Column('timezone', sa.String(64), server_default='UTC', nullable=False))
        if 'locale' not in user_cols:
            batch_op.add_column(sa.Column('locale', sa.String(10), server_default='en', nullable=False))
        if 'avatar_url' not in user_cols:
            batch_op.add_column(sa.Column('avatar_url', sa.String(255), nullable=True))

    # 2. Organizations table
    if 'organizations' not in existing_tables:
        op.create_table(
            'organizations',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('slug', sa.String(100), unique=True, index=True, nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('plan', sa.String(32), server_default='starter', nullable=False),
            sa.Column('logo_url', sa.String(255), nullable=True),
            sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('status', sa.String(32), server_default='active', nullable=False),
            sa.Column('settings_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )

    # 3. Organization Members table
    if 'organization_members' not in existing_tables:
        op.create_table(
            'organization_members',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('role', sa.String(32), server_default='member', nullable=False),
            sa.Column('title', sa.String(100), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('joined_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_org_member_unique', 'organization_members', ['organization_id', 'user_id'], unique=True)

    # 4. Organization Invitations table
    if 'organization_invitations' not in existing_tables:
        op.create_table(
            'organization_invitations',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('invited_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('email', sa.String(255), nullable=False, index=True),
            sa.Column('role', sa.String(32), server_default='member', nullable=False),
            sa.Column('token_hash', sa.String(64), unique=True, index=True, nullable=False),
            sa.Column('status', sa.String(32), server_default='pending', nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    # 5. Workspaces table updates
    ws_cols = [c['name'] for c in inspector.get_columns('workspaces')]
    with op.batch_alter_table('workspaces') as batch_op:
        if 'organization_id' not in ws_cols:
            batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
            batch_op.create_index('ix_workspaces_organization_id', ['organization_id'])
        if 'visibility' not in ws_cols:
            batch_op.add_column(sa.Column('visibility', sa.String(32), server_default='ORGANIZATION', nullable=False))
        if 'is_active' not in ws_cols:
            batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False))

    # 6. User Sessions table
    if 'user_sessions' not in existing_tables:
        op.create_table(
            'user_sessions',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('session_id', sa.String(64), unique=True, index=True, nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('refresh_token_hash', sa.String(255), nullable=True, index=True),
            sa.Column('device_name', sa.String(255), nullable=True),
            sa.Column('ip_address', sa.String(64), nullable=True),
            sa.Column('user_agent', sa.String(255), nullable=True),
            sa.Column('is_revoked', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('revoked_at', sa.DateTime(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('last_active_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    # 7. Password Reset Tokens table
    if 'password_reset_tokens' not in existing_tables:
        op.create_table(
            'password_reset_tokens',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('token_hash', sa.String(64), unique=True, index=True, nullable=False),
            sa.Column('is_used', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('used_at', sa.DateTime(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    # 8. Email Verification Tokens table
    if 'email_verification_tokens' not in existing_tables:
        op.create_table(
            'email_verification_tokens',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('token_hash', sa.String(64), unique=True, index=True, nullable=False),
            sa.Column('is_used', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('used_at', sa.DateTime(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

    # 9. Auth Audit Logs table
    if 'auth_audit_logs' not in existing_tables:
        op.create_table(
            'auth_audit_logs',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('user_id', sa.Integer(), nullable=True, index=True),
            sa.Column('event_type', sa.String(64), nullable=False, index=True),
            sa.Column('ip_address', sa.String(64), nullable=True),
            sa.Column('user_agent', sa.String(255), nullable=True),
            sa.Column('details_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

def downgrade() -> None:
    pass
