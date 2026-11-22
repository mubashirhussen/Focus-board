"""Add enterprise security compliance, SOC2/ISO27001 controls, risk register, trust center, and financial intelligence tables

Revision ID: 009_security_compliance_and_financial_intelligence
Revises: 008_enterprise_analytics_and_developer_platform
Create Date: 2026-11-22 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '009_security_compliance_and_financial_intelligence'
down_revision = '008_enterprise_analytics_and_developer_platform'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Compliance Controls
    op.create_table(
        'compliance_controls',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('control_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('framework', sa.String(length=32), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='NOT_ASSESSED', nullable=False),
        sa.Column('risk_level', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('remediation_notes', sa.Text(), nullable=True),
        sa.Column('last_reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('next_review_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_comp_ctrl_id', 'compliance_controls', ['control_id'])
    op.create_index('ix_comp_ctrl_fw', 'compliance_controls', ['framework'])
    op.create_index('ix_comp_ctrl_status', 'compliance_controls', ['status'])

    # 2. Compliance Evidences
    op.create_table(
        'compliance_evidences',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('control_id', sa.String(length=64), sa.ForeignKey('compliance_controls.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('evidence_type', sa.String(length=64), nullable=False),
        sa.Column('file_url', sa.String(length=512), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='VALIDATED', nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_comp_evi_ctrl', 'compliance_evidences', ['control_id'])

    # 3. Security Policies
    op.create_table(
        'security_policies',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('policy_key', sa.String(length=64), unique=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('version', sa.String(length=16), server_default='1.0', nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='DRAFT', nullable=False),
        sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('review_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_sec_pol_key', 'security_policies', ['policy_key'])

    # 4. Policy Acknowledgments
    op.create_table(
        'policy_acknowledgments',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('policy_id', sa.String(length=64), sa.ForeignKey('security_policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(length=16), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
    )
    op.create_index('ix_pol_ack_user', 'policy_acknowledgments', ['user_id'])

    # 5. Security Risk Items
    op.create_table(
        'security_risk_items',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('risk_code', sa.String(length=64), unique=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('likelihood', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('impact', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('risk_score', sa.Integer(), server_default='50', nullable=False),
        sa.Column('mitigation_plan', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='IDENTIFIED', nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('review_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_sec_risk_code', 'security_risk_items', ['risk_code'])
    op.create_index('ix_sec_risk_status', 'security_risk_items', ['status'])

    # 6. Security Incidents
    op.create_table(
        'security_incidents',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('incident_code', sa.String(length=64), unique=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('severity', sa.String(length=32), server_default='MEDIUM', nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='DETECTED', nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('contained_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('corrective_actions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_sec_inc_code', 'security_incidents', ['incident_code'])
    op.create_index('ix_sec_inc_status', 'security_incidents', ['status'])

    # 7. Security Vendors
    op.create_table(
        'security_vendors',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('service_type', sa.String(length=64), nullable=False),
        sa.Column('data_classification', sa.String(length=32), server_default='CONFIDENTIAL', nullable=False),
        sa.Column('risk_rating', sa.String(length=32), server_default='LOW', nullable=False),
        sa.Column('security_contact', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('review_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 8. Privacy Requests
    op.create_table(
        'privacy_requests',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('request_type', sa.String(length=32), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='RECEIVED', nullable=False),
        sa.Column('requester_email', sa.String(length=255), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_priv_req_status', 'privacy_requests', ['status'])

    # 9. Trust Center Documents
    op.create_table(
        'trust_center_documents',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=128), unique=True, nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('version', sa.String(length=16), server_default='1.0', nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_trust_doc_slug', 'trust_center_documents', ['slug'])

    # 10. Financial Transactions
    op.create_table(
        'financial_transactions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('customer_id', sa.String(length=100), nullable=True),
        sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('subscriptions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('transaction_type', sa.String(length=32), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=8), server_default='USD', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='SUCCEEDED', nullable=False),
        sa.Column('invoice_id', sa.String(length=64), nullable=True),
        sa.Column('provider_tx_id', sa.String(length=128), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_fin_tx_tenant', 'financial_transactions', ['tenant_id'])
    op.create_index('ix_fin_tx_created', 'financial_transactions', ['created_at'])

    # 11. Financial Metric Snapshots
    op.create_table(
        'financial_metric_snapshots',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('period_date', sa.String(length=32), nullable=False),
        sa.Column('mrr_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('arr_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('gross_revenue_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('net_revenue_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('new_mrr_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('expansion_mrr_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('contraction_mrr_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('churned_mrr_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('active_subscriptions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('paying_customers', sa.Integer(), server_default='0', nullable=False),
        sa.Column('churned_customers', sa.Integer(), server_default='0', nullable=False),
        sa.Column('currency', sa.String(length=8), server_default='USD', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_fin_snap_period', 'financial_metric_snapshots', ['period_date'])

    # 12. Cost Records
    op.create_table(
        'cost_records',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('amount_cents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('currency', sa.String(length=8), server_default='USD', nullable=False),
        sa.Column('billing_period', sa.String(length=32), nullable=False),
        sa.Column('cost_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_cost_tenant', 'cost_records', ['tenant_id'])
    op.create_index('ix_cost_date', 'cost_records', ['cost_date'])

    # 13. Financial Budgets
    op.create_table(
        'financial_budgets',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('budget_amount_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=8), server_default='USD', nullable=False),
        sa.Column('period', sa.String(length=32), server_default='MONTHLY', nullable=False),
        sa.Column('alert_threshold_percentage', sa.Float(), server_default='80.0', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_budget_tenant', 'financial_budgets', ['tenant_id'])

    # 14. Financial Forecasts
    op.create_table(
        'financial_forecasts',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('scenario_name', sa.String(length=32), server_default='BASELINE', nullable=False),
        sa.Column('target_period', sa.String(length=32), nullable=False),
        sa.Column('projected_mrr_cents', sa.Integer(), nullable=False),
        sa.Column('projected_arr_cents', sa.Integer(), nullable=False),
        sa.Column('projected_churn_rate', sa.Float(), server_default='2.5', nullable=False),
        sa.Column('assumptions_json', sa.Text(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('financial_forecasts')
    op.drop_table('financial_budgets')
    op.drop_table('cost_records')
    op.drop_table('financial_metric_snapshots')
    op.drop_table('financial_transactions')
    op.drop_table('trust_center_documents')
    op.drop_table('privacy_requests')
    op.drop_table('security_vendors')
    op.drop_table('security_incidents')
    op.drop_table('security_risk_items')
    op.drop_table('policy_acknowledgments')
    op.drop_table('security_policies')
    op.drop_table('compliance_evidences')
    op.drop_table('compliance_controls')
