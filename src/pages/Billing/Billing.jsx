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
} from 'lucide-react';
import { billingApi } from '../../services/billingApi';
import { useAuth } from '../../context/AuthContext';
import './Billing.css';

export function Billing() {
  const { isAuthenticated } = useAuth();
  const [plans, setPlans] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [usage, setUsage] = useState(null);
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
      setPlans(plansData || []);
      setSubscription(subData);
      setUsage(usageData);
    } catch (err) {
      console.error('Failed to load billing details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBillingData();
  }, [isAuthenticated]);

  const handleCheckout = async (planId) => {
    if (!isAuthenticated) {
      alert('Please sign in to select or upgrade a subscription plan.');
      return;
    }
    setActionLoading(true);
    setMessage('');
    try {
      const res = await billingApi.changePlan(planId);
      setMessage(`Successfully switched to the ${res.plan.name} plan!`);
      loadBillingData();
    } catch (err) {
      setMessage(`Unable to change plan: ${err.message}`);
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
      setMessage(`Cancellation failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const currentPlanSlug = subscription?.plan?.slug || 'free';

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

      {/* Usage Metering Section (when authenticated) */}
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
                    <span className="usage-metric-name">{m.metric_name.replace(/_/g, ' ').toUpperCase()}</span>
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

      {/* Subscription Settings & Invoices */}
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
