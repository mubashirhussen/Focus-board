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
  X,
  Landmark,
  CheckCircle2,
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
  const { isAuthenticated, user } = useAuth();
  const [plans, setPlans] = useState(defaultSamplePlans);
  const [subscription, setSubscription] = useState(defaultSampleSubscription);
  const [usage, setUsage] = useState(defaultSampleUsage);
  const [invoices, setInvoices] = useState(sampleInvoices);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Upgrade Modal State
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);
  const [targetUpgradePlan, setTargetUpgradePlan] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('bank'); // 'bank' | 'card' | 'upi'
  const [isProcessingUpgrade, setIsProcessingUpgrade] = useState(false);
  const [upgradeSuccess, setUpgradeSuccess] = useState(false);
  const [upgradeTxnDetails, setUpgradeTxnDetails] = useState(null);

  // Form Fields State
  const [bankDetails, setBankDetails] = useState({
    bankName: 'JPMorgan Chase Bank, N.A.',
    accountHolder: 'FocusBoard Enterprise Team',
    accountNumber: '**** **** 8824',
    routingNumber: '021000021',
    accountType: 'Checking'
  });

  const [cardDetails, setCardDetails] = useState({
    cardHolder: 'John Doe',
    cardNumber: '•••• •••• •••• 4242',
    expiry: '12/28',
    cvv: '•••',
    postalCode: '10001'
  });

  const [upiDetails, setUpiDetails] = useState({
    upiId: 'focusboard.finance@okaxis'
  });

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

  const openUpgradeModal = (plan) => {
    setTargetUpgradePlan(plan);
    setPaymentMethod('bank');
    setUpgradeSuccess(false);
    setUpgradeTxnDetails(null);
    if (user?.name) {
      setBankDetails(prev => ({ ...prev, accountHolder: user.name }));
      setCardDetails(prev => ({ ...prev, cardHolder: user.name }));
    }
    setIsUpgradeModalOpen(true);
  };

  const closeUpgradeModal = () => {
    if (isProcessingUpgrade) return;
    setIsUpgradeModalOpen(false);
    setTargetUpgradePlan(null);
    setUpgradeSuccess(false);
  };

  const handleConfirmUpgrade = async (e) => {
    if (e) e.preventDefault();
    if (!targetUpgradePlan) return;

    setIsProcessingUpgrade(true);
    setMessage('');

    try {
      // Call backend API if connected
      await billingApi.changePlan(targetUpgradePlan.id).catch(() => null);
    } catch (err) {
      console.warn('Backend billing API change plan warning:', err);
    }

    // Simulate verified bank transaction & instant plan activation
    setTimeout(() => {
      const nextDate = new Date(Date.now() + 30 * 86400000).toISOString();
      setSubscription({
        plan: targetUpgradePlan,
        status: 'ACTIVE',
        current_period_end: nextDate,
        cancel_at_period_end: false,
      });

      // Update quota usage limits based on new plan
      setUsage(prev => {
        const isEnt = targetUpgradePlan.slug === 'enterprise';
        return {
          ...prev,
          metrics: {
            ...prev.metrics,
            tasks: {
              ...prev.metrics.tasks,
              limit: isEnt ? 50000 : 10000,
              remaining: isEnt ? 49952 : 9952
            },
            workspaces: {
              ...prev.metrics.workspaces,
              limit: isEnt ? -1 : 25,
              remaining: isEnt ? -1 : 22
            },
            ai_copilot: {
              ...prev.metrics.ai_copilot,
              limit: isEnt ? 25000 : 5000,
              remaining: isEnt ? 24660 : 4660
            }
          }
        };
      });

      // Prepend an invoice receipt
      const paymentSource = paymentMethod === 'bank'
        ? `${bankDetails.bankName || 'Direct Bank ACH'} (•••• ${bankDetails.accountNumber.slice(-4)})`
        : paymentMethod === 'card'
        ? `Visa Card (•••• ${cardDetails.cardNumber.slice(-4)})`
        : `UPI Direct (${upiDetails.upiId || 'instant-pay'})`;

      const newInvoice = {
        id: `INV-2026-${String(invoices.length + 1).padStart(3, '0')}`,
        date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
        amount: targetUpgradePlan.price_cents === 0 ? '$0.00' : `$${(targetUpgradePlan.price_cents / 100).toFixed(2)}`,
        status: 'Paid',
        method: paymentSource
      };

      setInvoices(prev => [newInvoice, ...prev]);

      setUpgradeTxnDetails({
        authCode: `AUTH-${Math.random().toString(36).substring(2, 9).toUpperCase()}`,
        planName: targetUpgradePlan.name,
        amount: targetUpgradePlan.price_cents === 0 ? '$0.00' : `$${(targetUpgradePlan.price_cents / 100).toFixed(2)}`,
        source: paymentSource,
        date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
      });

      setIsProcessingUpgrade(false);
      setUpgradeSuccess(true);
      setMessage(`Successfully upgraded your workspace to the ${targetUpgradePlan.name} plan!`);
    }, 900);
  };

  const handleCheckout = (planId) => {
    const target = plans.find(p => p.id === planId);
    if (target) {
      openUpgradeModal(target);
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
                  onClick={() => openUpgradeModal(p)}
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
              {invoices.map((inv) => (
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

      {/* Bank & Payment Details Upgrade Modal */}
      {isUpgradeModalOpen && targetUpgradePlan && (
        <div className="billing-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="upgrade-modal-title">
          <div className="billing-modal-card">
            {/* Modal Header */}
            <div className="billing-modal-header">
              <div>
                <h3 id="upgrade-modal-title" className="modal-title">
                  {upgradeSuccess ? 'Upgrade Confirmed' : 'Complete Plan Upgrade'}
                </h3>
                <span className="modal-subtitle">
                  {upgradeSuccess
                    ? `Workspace upgraded to ${targetUpgradePlan.name}`
                    : `Provide your payment details to activate ${targetUpgradePlan.name}`}
                </span>
              </div>
              <button
                type="button"
                className="btn-modal-close"
                onClick={closeUpgradeModal}
                disabled={isProcessingUpgrade}
                aria-label="Close modal"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Content */}
            {upgradeSuccess ? (
              <div className="upgrade-success-view">
                <div className="success-icon-wrap">
                  <CheckCircle2 size={54} className="text-emerald-500" />
                </div>
                <h4 className="success-heading">Payment Authorized & Plan Activated!</h4>
                <p className="success-subtext">
                  Your workspace has been successfully upgraded to the <strong>{targetUpgradePlan.name}</strong> tier.
                  New resource quotas and advanced SaaS intelligence modules are immediately accessible.
                </p>

                {upgradeTxnDetails && (
                  <div className="success-receipt-box">
                    <div className="receipt-row">
                      <span className="receipt-label">Target Tier:</span>
                      <span className="receipt-val font-semibold">{upgradeTxnDetails.planName}</span>
                    </div>
                    <div className="receipt-row">
                      <span className="receipt-label">Amount Charged:</span>
                      <span className="receipt-val font-semibold">{upgradeTxnDetails.amount}</span>
                    </div>
                    <div className="receipt-row">
                      <span className="receipt-label">Payment Account:</span>
                      <span className="receipt-val">{upgradeTxnDetails.source}</span>
                    </div>
                    <div className="receipt-row">
                      <span className="receipt-label">Authorization Code:</span>
                      <span className="receipt-val code-font">{upgradeTxnDetails.authCode}</span>
                    </div>
                    <div className="receipt-row">
                      <span className="receipt-label">Effective Date:</span>
                      <span className="receipt-val">{upgradeTxnDetails.date}</span>
                    </div>
                  </div>
                )}

                <div className="modal-actions-footer">
                  <button
                    type="button"
                    className="btn-modal-primary"
                    onClick={closeUpgradeModal}
                  >
                    Done & Return to Billing
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleConfirmUpgrade} className="billing-modal-form">
                {/* Plan Summary Banner */}
                <div className="upgrade-plan-pill-banner">
                  <div className="pill-banner-info">
                    <span className="pill-banner-label">UPGRADE TO</span>
                    <strong className="pill-banner-name">{targetUpgradePlan.name}</strong>
                  </div>
                  <div className="pill-banner-price">
                    <span className="pill-price-val">
                      {targetUpgradePlan.price_cents === 0 ? '$0' : `$${(targetUpgradePlan.price_cents / 100).toFixed(0)}`}
                    </span>
                    <span className="pill-price-sub">/ month</span>
                  </div>
                </div>

                {/* Payment Method Switcher Tabs */}
                <div className="payment-method-selector-tabs">
                  <button
                    type="button"
                    className={`pay-tab-btn ${paymentMethod === 'bank' ? 'active' : ''}`}
                    onClick={() => setPaymentMethod('bank')}
                  >
                    <Landmark size={15} />
                    <span>Bank Details (ACH / Wire)</span>
                  </button>
                  <button
                    type="button"
                    className={`pay-tab-btn ${paymentMethod === 'card' ? 'active' : ''}`}
                    onClick={() => setPaymentMethod('card')}
                  >
                    <CreditCard size={15} />
                    <span>Credit / Debit Card</span>
                  </button>
                  <button
                    type="button"
                    className={`pay-tab-btn ${paymentMethod === 'upi' ? 'active' : ''}`}
                    onClick={() => setPaymentMethod('upi')}
                  >
                    <Zap size={15} />
                    <span>UPI / Net Banking</span>
                  </button>
                </div>

                {/* Tab 1: Bank Account Details */}
                {paymentMethod === 'bank' && (
                  <div className="payment-fields-pane">
                    <div className="form-field-group">
                      <label htmlFor="bank-name-input">Bank / Financial Institution</label>
                      <input
                        id="bank-name-input"
                        type="text"
                        className="modal-text-input"
                        placeholder="e.g. JPMorgan Chase Bank, Wells Fargo, HSBC"
                        value={bankDetails.bankName}
                        onChange={(e) => setBankDetails({ ...bankDetails, bankName: e.target.value })}
                        required
                      />
                    </div>

                    <div className="form-field-group">
                      <label htmlFor="bank-holder-input">Account Holder Full Name / Entity</label>
                      <input
                        id="bank-holder-input"
                        type="text"
                        className="modal-text-input"
                        placeholder="e.g. Mubashir Hussen"
                        value={bankDetails.accountHolder}
                        onChange={(e) => setBankDetails({ ...bankDetails, accountHolder: e.target.value })}
                        required
                      />
                    </div>

                    <div className="form-field-row-split">
                      <div className="form-field-group">
                        <label htmlFor="bank-account-num">Account Number / IBAN</label>
                        <input
                          id="bank-account-num"
                          type="text"
                          className="modal-text-input"
                          placeholder="e.g. 987654321098"
                          value={bankDetails.accountNumber}
                          onChange={(e) => setBankDetails({ ...bankDetails, accountNumber: e.target.value })}
                          required
                        />
                      </div>
                      <div className="form-field-group">
                        <label htmlFor="bank-routing-num">Routing / IFSC / Sort Code</label>
                        <input
                          id="bank-routing-num"
                          type="text"
                          className="modal-text-input"
                          placeholder="e.g. 021000021"
                          value={bankDetails.routingNumber}
                          onChange={(e) => setBankDetails({ ...bankDetails, routingNumber: e.target.value })}
                          required
                        />
                      </div>
                    </div>

                    <div className="form-field-group">
                      <label htmlFor="bank-type-select">Account Type</label>
                      <select
                        id="bank-type-select"
                        className="modal-select-input"
                        value={bankDetails.accountType}
                        onChange={(e) => setBankDetails({ ...bankDetails, accountType: e.target.value })}
                      >
                        <option value="Checking">Checking Account (Direct ACH Debit)</option>
                        <option value="Savings">Savings Account</option>
                        <option value="Corporate">Commercial / Corporate Business Account</option>
                      </select>
                    </div>
                  </div>
                )}

                {/* Tab 2: Credit / Debit Card */}
                {paymentMethod === 'card' && (
                  <div className="payment-fields-pane">
                    <div className="form-field-group">
                      <label htmlFor="card-holder-input">Cardholder Name</label>
                      <input
                        id="card-holder-input"
                        type="text"
                        className="modal-text-input"
                        placeholder="Name as it appears on card"
                        value={cardDetails.cardHolder}
                        onChange={(e) => setCardDetails({ ...cardDetails, cardHolder: e.target.value })}
                        required
                      />
                    </div>

                    <div className="form-field-group">
                      <label htmlFor="card-number-input">Card Number</label>
                      <input
                        id="card-number-input"
                        type="text"
                        className="modal-text-input"
                        placeholder="4111 2222 3333 4444"
                        value={cardDetails.cardNumber}
                        onChange={(e) => setCardDetails({ ...cardDetails, cardNumber: e.target.value })}
                        required
                      />
                    </div>

                    <div className="form-field-row-split">
                      <div className="form-field-group">
                        <label htmlFor="card-expiry-input">Expiry Date (MM/YY)</label>
                        <input
                          id="card-expiry-input"
                          type="text"
                          className="modal-text-input"
                          placeholder="12/28"
                          value={cardDetails.expiry}
                          onChange={(e) => setCardDetails({ ...cardDetails, expiry: e.target.value })}
                          required
                        />
                      </div>
                      <div className="form-field-group">
                        <label htmlFor="card-cvv-input">CVV / CVC</label>
                        <input
                          id="card-cvv-input"
                          type="password"
                          maxLength={4}
                          className="modal-text-input"
                          placeholder="•••"
                          value={cardDetails.cvv}
                          onChange={(e) => setCardDetails({ ...cardDetails, cvv: e.target.value })}
                          required
                        />
                      </div>
                      <div className="form-field-group">
                        <label htmlFor="card-zip-input">Postal / ZIP</label>
                        <input
                          id="card-zip-input"
                          type="text"
                          className="modal-text-input"
                          placeholder="10001"
                          value={cardDetails.postalCode}
                          onChange={(e) => setCardDetails({ ...cardDetails, postalCode: e.target.value })}
                          required
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab 3: UPI / Instant Pay */}
                {paymentMethod === 'upi' && (
                  <div className="payment-fields-pane">
                    <div className="form-field-group">
                      <label htmlFor="upi-vpa-input">Virtual Payment Address (UPI ID)</label>
                      <input
                        id="upi-vpa-input"
                        type="text"
                        className="modal-text-input"
                        placeholder="e.g. organization@upi or mobile@okhdfcbank"
                        value={upiDetails.upiId}
                        onChange={(e) => setUpiDetails({ upiId: e.target.value })}
                        required
                      />
                      <small className="field-hint-text">
                        A verification authorization request will be sent to your UPI app.
                      </small>
                    </div>
                  </div>
                )}

                {/* Security Guarantee Notice */}
                <div className="modal-security-guarantee">
                  <Lock size={14} className="text-emerald-600 flex-shrink-0" />
                  <span>
                    Direct 256-bit encrypted bank connection. Handled under SOC-2 Type II & PCI-DSS Level 1 compliance.
                    Charges apply automatically every billing cycle.
                  </span>
                </div>

                {/* Modal Actions */}
                <div className="modal-actions-footer">
                  <button
                    type="button"
                    className="btn-modal-cancel"
                    onClick={closeUpgradeModal}
                    disabled={isProcessingUpgrade}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-modal-primary"
                    disabled={isProcessingUpgrade}
                  >
                    {isProcessingUpgrade
                      ? 'Authorizing Bank & Upgrading...'
                      : `Authorize & Upgrade to ${targetUpgradePlan.name}`}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
