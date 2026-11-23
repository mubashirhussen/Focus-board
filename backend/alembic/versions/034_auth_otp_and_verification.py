"""Auth: Email OTP Verifications, Passwordless Authentication and Google OAuth Identity

Revision ID: 034_auth_otp_and_verification
Revises: 033_b22_security_intelligence_hardening
Create Date: 2026-11-23 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '034_auth_otp_and_verification'
down_revision = '033_b22_security_intelligence_hardening'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Create email_otp_verifications table
    if 'email_otp_verifications' not in existing_tables:
        op.create_table(
            'email_otp_verifications',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('session_id', sa.String(64), unique=True, index=True, nullable=False),
            sa.Column('email', sa.String(255), index=True, nullable=False),
            sa.Column('otp_hash', sa.String(64), nullable=False),
            sa.Column('purpose', sa.String(32), server_default='login', nullable=False),
            sa.Column('metadata_json', sa.Text(), server_default='{}', nullable=False),
            sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
            sa.Column('max_attempts', sa.Integer(), server_default='5', nullable=False),
            sa.Column('is_verified', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('is_consumed', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('last_sent_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )

def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'email_otp_verifications' in existing_tables:
        op.drop_table('email_otp_verifications')
