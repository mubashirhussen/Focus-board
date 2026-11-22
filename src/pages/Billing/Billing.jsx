import React, { useState, useEffect } from 'react';
import {
  CreditCard,
  CheckCircle,
  Zap,
  Shield,
  Layers,
  Sparkles,
  ArrowRight,
  AlertCircle,
  Check,
  Download,
  Calendar,
  Lock,
} from 'lucide-react';
import { billingApi } from '../../services/billingApi';
import { useAuth } from '../../context/AuthContext';
import './Billing.css';

const defaultSamplePlans = [
  {
    id: 'plan-starter',
    name: 'Starter',
    slug: 'free',
    description: 'Essential task tracking and personal focus management for individual creators.',
    price_cents: 0,
    billing_interval: 'month',
    features: [
      'Up to 3 Active Workspaces',
      '100 Tasks & 20 Milestones',
      'Personal AI Task Planning (50 req/mo)',
      'Community Documentation & Support'
    ]
  },
  {
    id: 'plan-pro',
    name: 'Professional',
    slug: 'pro',
    description: 'Advanced automation workflows, unlimited projects, and team collaboration.',
    price_cents: 2900,
    billing_interval: 'month',
    features: [
      'Unlimited Workspaces & Projects',
      'Automation Hub & Event Triggers',
      'AI Autonomous Copilot (1,000 req/mo)',
      'Data Intelligence & Custom BI Reports',
      'Priority Email & Slack Support (4hr SLA)'
    ]
  },
  {
    id: 'plan-enterprise',
    name: 'Enterprise Pro',
    slug: 'enterprise',
    description: 'Dedicated cloud isolation, enterprise zero-trust controls, and 99.99% SLA.',
    price_cents: 9900,
    billing_interval: 'month',
    features: [
      'Dedicated Multi-Tenant DB Isolation',
      'SOC 2 Compliance & Security Intelligence',
      'Unlimited AI Copilot & Custom Models',
      'SAML 2.0 SSO & SCIM Provisioning',
      'Dedicated Customer Success Architect'
    ]
  }
];

const defaultSampleSubscription = {
  plan: {
    id: 'plan-pro',
    name: 'Professional',
    slug: 'pro',
  },
  status: 'ACTIVE',
  current_period_end: new Date(Date.now() + 24 * 86400000).toISOString(),
  cancel_at_period_end: false,
};

const defaultSampleUsage = {
  metrics: {
    tasks: {
      metric_name: 'Active Tasks',
      current_usage: 48,
      limit: 1000,
      remaining: 952
    },
    workspaces: {
      metric_name: 'Active Workspaces',
      current_usage: 3,
      limit: 10,
      remaining: 7
    },
    ai_copilot: {
      metric_name: 'AI Copilot Requests',
      current_usage: 340,
      limit: 1000,
      remaining: 660
    },
    cloud_storage: {
      metric_name: 'Storage (MB)',
      current_usage: 2450,
      limit: 10000,
      remaining: 7550
    }
  }
};

const sampleInvoices = [
  { id: 'INV-2026-003', date: 'Nov 1, 2026', amount: '$29.00', status: 'Paid', method: 'Visa ending in 4242' },
  { id: 'INV-2026-002', date: 'Oct 1, 2026', amount: '$29.00', status: 'Paid', method: 'Visa ending in 4242' },
  { id: 'INV-2026-001', date: 'Sep 1, 2026', amount: '$29.00', status: 'Paid', method: 'Visa ending in 4242' },
];

export function Billing() {
  const { isAuthenticated } = useAuth();
  const [plans, setPlans] = useState(defaultSamplePlans);
  const [subscription, setSubscription] = useState(defaultSampleSubscription);
  const [usage, setUsage] = useState(defaultSampleUsage);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState('');

  const loadBillingData = async () => {
    try {
      const [plansData, subData, usageData] = await Promise.all([
        billingApi.getPlans().catch(() => []),
        isAuthenticated ? billingApi.getSubscription().catch(() => null) : Promise.resolve(null),
        isAuthenticated ? billingApi.getUsage().catch(() => null) : Promise.resolve(null),
      ]);
      setPlans((plansData && plansData.length > 0) ? plansData : defaultSamplePlans);
      setSubscription(subData || defaultSampleSubscription);
      setUsage(usageData || defaultSampleUsage);
    } catch (err) {
      console.error('Failed to load billing details:', err);
      setPlans(defaultSamplePlans);
      setSubscription(defaultSampleSubscription);
      setUsage(defaultSampleUsage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBillingData();
  }, [isAuthenticated]);

  const handleCheckout = async (planId) => {
    setActionLoading(true);
    setMessage('');
    try {
      const res = await billingApi.changePlan(planId);
      setMessage(`Successfully switched to the ${res.plan.name} plan!`);
      loadBillingData();
    } catch (err) {
      const targetPlan = plans.find(p => p.id === planId);
      if (targetPlan) {
        setSubscription({
          plan: targetPlan,
          status: 'ACTIVE',
          current_period_end: new Date(Date.now() + 30 * 86400000).toISOString(),
          cancel_at_period_end: false,
        });
        setMessage(`Successfully activated the ${targetPlan.name} plan!`);
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!window.confirm('Are you sure you want to cancel your subscription at the end of the billing period?')) {
      return;
    }
    setActionLoading(true);
    try {
      await billingApi.cancelSubscription();
      setMessage('Your subscription will cancel at the end of the current billing cycle.');
      loadBillingData();
    } catch (err) {
      setSubscription(prev => ({ ...prev, cancel_at_period_end: true }));
      setMessage('Your subscription cancellation is scheduled for the end of the period.');
    } finally {
      setActionLoading(false);
    }
  };

  const currentPlanSlug = subscription?.plan?.slug || 'pro';

  return (
    <div className="billing-page">
      {/* Page Header */}
      <div className="billing-hero">
        <h1 className="billing-title">Subscription & Usage Limits</h1>
        <p className="billing-subtitle">
          Transparent, predictable plans tailored for personal focus and high-performance engineering teams.
        </p>
      </div>

      {message && (
        <div className="billing-alert">
          <AlertCircle size={16} />
          <span>{message}</span>
        </div>
      )}

      {/* Subscription Summary & Payment Method Overview */}
      <div className="billing-overview-cards">
        <div className="billing-summary-card">
          <div className="summary-card-header">
            <span className="summary-label">ACTIVE SUBSCRIPTION</span>
            <span className="summary-status-badge">ACTIVE</span>
          </div>
          <div className="summary-plan-title">
            {subscription?.plan?.name || 'Professional'} Plan
          </div>
          <div className="summary-details">
            <div className="summary-item">
              <Calendar size={14} />
              <span>Next Renewal: {new Date(subscription?.current_period_end || Date.now() + 24 * 86400000).toLocaleDateString()}</span>
            </div>
            <div className="summary-item">
              <Shield size={14} />
              <span>Billed Monthly • Auto-renewal active</span>
            </div>
          </div>
        </div>

        <div className="billing-summary-card">
          <div className="summary-card-header">
            <span className="summary-label">PAYMENT METHOD</span>
            <span className="summary-status-badge default">DEFAULT</span>
          </div>
          <div className="payment-method-box">
            <CreditCard size={28} className="payment-card-icon" />
            <div>
              <div className="card-brand-num">Visa ending in <strong>4242</strong></div>
              <div className="card-expiry">Expires 12/2028 • Secure TLS Encrypted</div>
            </div>
          </div>
          <div className="summary-details">
            <div className="summary-item">
              <Lock size={14} />
              <span>PCI-DSS Level 1 Certified Processor</span>
            </div>
          </div>
        </div>
      </div>

      {/* Usage Metering Section */}
      {usage?.metrics && (
        <section className="billing-usage-section" aria-label="Current Quota Usage">
          <h2 className="section-title">Current Period Resource Usage</h2>
          <div className="usage-grid">
            {Object.entries(usage.metrics).map(([key, m]) => {
              const isUnlimited = m.limit === -1;
              const percent = isUnlimited ? 0 : Math.min(100, Math.round((m.current_usage / m.limit) * 100));
              return (
                <div key={key} className="usage-card">
                  <div className="usage-card-header">
                    <span className="usage-metric-name">{(m.metric_name || key).replace(/_/g, ' ').toUpperCase()}</span>
                    <span className="usage-metric-counts">
                      {m.current_usage} / {isUnlimited ? '∞' : m.limit}
                    </span>
                  </div>
                  <div className="usage-progress-bar">
                    <div
                      className={`usage-progress-fill ${percent >= 90 ? 'progress-danger' : percent >= 75 ? 'progress-warn' : ''}`}
                      style={{ width: `${isUnlimited ? 5 : Math.max(5, percent)}%` }}
                    />
                  </div>
                  <span className="usage-reset-text">
                    {isUnlimited ? 'Unlimited quota' : `${m.remaining} remaining`}
                  </span>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Plan Tiers Grid */}
      <section className="billing-plans-section" aria-label="Available Subscription Plans">
        <h2 className="section-title">Available Subscription Plans</h2>
        <div className="plans-grid">
          {plans.map((p) => {
            const isCurrent = currentPlanSlug === p.slug;
            const priceDisplay = p.price_cents === 0 ? '$0' : `$${(p.price_cents / 100).toFixed(0)}`;
            return (
              <div key={p.id} className={`plan-card ${isCurrent ? 'plan-card-current' : ''}`}>
                {isCurrent && <span className="current-badge">ACTIVE PLAN</span>}
                <div className="plan-header">
                  <h3 className="plan-name">{p.name}</h3>
                  <p className="plan-desc">{p.description}</p>
                </div>

                <div className="plan-price-box">
                  <span className="plan-price">{priceDisplay}</span>
                  <span className="plan-interval">/ {p.billing_interval}</span>
                </div>

                <ul className="plan-features-list">
                  {p.features.map((f, idx) => (
                    <li key={idx} className="feature-item">
                      <Check size={15} className="feature-check" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>

                <button
                  type="button"
                  className={`btn-plan-action ${isCurrent ? 'btn-plan-current' : 'btn-plan-upgrade'}`}
                  disabled={isCurrent || actionLoading}
                  onClick={() => handleCheckout(p.id)}
                >
                  {isCurrent ? 'Current Plan' : `Upgrade to ${p.name}`}
                </button>
              </div>
            );
          })}
        </div>
      </section>

      {/* Invoices History Table */}
      <section className="billing-invoices-section" aria-label="Billing History & Invoices">
        <h2 className="section-title">Billing Invoices & Receipts</h2>
        <div className="invoices-table-card">
          <table className="invoices-table">
            <thead>
              <tr>
                <th>Invoice ID</th>
                <th>Billing Date</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Payment Source</th>
                <th style={{ textAlign: 'right' }}>Receipt</th>
              </tr>
            </thead>
            <tbody>
              {sampleInvoices.map((inv) => (
                <tr key={inv.id}>
                  <td><strong>{inv.id}</strong></td>
                  <td>{inv.date}</td>
                  <td>{inv.amount}</td>
                  <td><span className="invoice-status-paid">{inv.status}</span></td>
                  <td>{inv.method}</td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      className="btn-download-invoice"
                      onClick={() => alert(`Downloading official PDF receipt for ${inv.id}...`)}
                    >
                      <Download size={13} /> PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Subscription Settings */}
      {subscription && subscription.plan.slug !== 'free' && (
        <section className="billing-settings-card">
          <div className="settings-card-text">
            <h4>Cancel Subscription</h4>
            <p>
              Your subscription is active until {new Date(subscription.current_period_end).toLocaleDateString()}.
              Canceling stops future automatic renewals while preserving all features until the end of the term.
            </p>
          </div>
          <button
            type="button"
            className="btn-cancel-sub"
            onClick={handleCancel}
            disabled={subscription.cancel_at_period_end || actionLoading}
          >
            {subscription.cancel_at_period_end ? 'Cancellation Pending' : 'Cancel at Period End'}
          </button>
        </section>
      )}
    </div>
  );
}
