import React, { useState, useEffect } from 'react';
import {
  DollarSign,
  TrendingUp,
  CreditCard,
  PieChart,
  BarChart3,
  Download,
  AlertTriangle,
  Plus,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet
} from 'lucide-react';
import { financialIntelligenceApi } from '../../services/financialIntelligenceApi';
import './FinancialDashboard.css';

export default function FinancialDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Financial Data
  const [overview, setOverview] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [costs, setCosts] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [forecasts, setForecasts] = useState([]);

  // Modals & Actions
  const [showTxModal, setShowTxModal] = useState(false);
  const [newTx, setNewTx] = useState({
    transaction_type: 'SUBSCRIPTION_PAYMENT',
    amount: 199.00,
    status: 'SUCCEEDED',
    description: 'Enterprise Seat Expansion'
  });

  const [showBudgetModal, setShowBudgetModal] = useState(false);
  const [newBudget, setNewBudget] = useState({
    category: 'CLOUD',
    budget_amount: 1000.00,
    period: 'MONTHLY',
    alert_threshold_percentage: 80.0
  });

  const [exportType, setExportType] = useState('EXECUTIVE_SUMMARY');
  const [actionSuccess, setActionSuccess] = useState('');

  const loadFinancialData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [ovData, txData, costData, bdgData, fcData] = await Promise.all([
        financialIntelligenceApi.getOverview(),
        financialIntelligenceApi.listTransactions(),
        financialIntelligenceApi.listCosts(),
        financialIntelligenceApi.listBudgets(),
        financialIntelligenceApi.listForecasts()
      ]);
      setOverview(ovData);
      setTransactions(txData);
      setCosts(costData);
      setBudgets(bdgData);
      setForecasts(fcData);
    } catch (err) {
      console.error('Failed to load financial data:', err);
      setError('Unable to load SaaS financial intelligence. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFinancialData();
  }, []);

  const handleRecordTransaction = async (e) => {
    e.preventDefault();
    try {
      await financialIntelligenceApi.recordTransaction({
        tenant_id: 'default',
        transaction_type: newTx.transaction_type,
        amount_cents: Math.round(Number(newTx.amount) * 100),
        status: newTx.status,
        description: newTx.description
      });
      setShowTxModal(false);
      setNewTx({
        transaction_type: 'SUBSCRIPTION_PAYMENT',
        amount: 199.00,
        status: 'SUCCEEDED',
        description: ''
      });
      setActionSuccess('Financial transaction recorded successfully.');
      setTimeout(() => setActionSuccess(''), 3000);
      loadFinancialData();
    } catch (err) {
      console.error('Failed to record transaction:', err);
    }
  };

  const handleCreateBudget = async (e) => {
    e.preventDefault();
    try {
      await financialIntelligenceApi.createBudget({
        tenant_id: 'default',
        category: newBudget.category,
        budget_amount_cents: Math.round(Number(newBudget.budget_amount) * 100),
        period: newBudget.period,
        alert_threshold_percentage: Number(newBudget.alert_threshold_percentage),
        status: 'ACTIVE'
      });
      setShowBudgetModal(false);
      setActionSuccess('Financial spending budget registered.');
      setTimeout(() => setActionSuccess(''), 3000);
      loadFinancialData();
    } catch (err) {
      console.error('Failed to create budget:', err);
    }
  };

  const handleExportCSV = async () => {
    try {
      const resp = await financialIntelligenceApi.exportReport(exportType, 'CSV');
      const blob = new Blob([resp.content], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', resp.report_name);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setActionSuccess(`Exported ${resp.report_name}`);
      setTimeout(() => setActionSuccess(''), 3500);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  if (loading && !overview) {
    return (
      <div className="finance-loading-container">
        <RefreshCw className="animate-spin text-primary" size={32} />
        <p>Aggregating SaaS Financial Intelligence & FinOps Telemetry...</p>
      </div>
    );
  }

  return (
    <div className="financial-dashboard-container">
      {/* Header */}
      <div className="finance-header">
        <div>
          <h1 className="finance-title">
            <DollarSign className="title-icon" /> SaaS Financial Intelligence & FinOps
          </h1>
          <p className="finance-subtitle">
            Normalized MRR/ARR analytics, unit economics, cloud/AI gross margin, and budget thresholds.
          </p>
        </div>
        <div className="finance-header-actions">
          <select
            className="export-select"
            value={exportType}
            onChange={(e) => setExportType(e.target.value)}
          >
            <option value="EXECUTIVE_SUMMARY">Executive Summary</option>
            <option value="TRANSACTIONS">Transaction Ledger</option>
            <option value="FINOPS_COSTS">FinOps Direct Costs</option>
          </select>
          <button className="btn-primary" onClick={handleExportCSV}>
            <Download size={16} /> Export CSV
          </button>
          <button className="btn-secondary" onClick={loadFinancialData} title="Refresh Telemetry">
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {actionSuccess && (
        <div className="alert-banner success-banner">
          <CheckCircle2 size={18} /> {actionSuccess}
        </div>
      )}

      {error && (
        <div className="alert-banner error-banner">
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* KPI Ribbon */}
      {overview && (
        <div className="kpi-ribbon-grid">
          <div className="kpi-card highlight-card">
            <span className="kpi-label">Monthly Recurring Revenue</span>
            <div className="kpi-value">${overview.total_mrr.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
            <span className="kpi-subtext">Active paying tenants: {overview.mrr_breakdown.paying_tenants_count}</span>
          </div>
          <div className="kpi-card">
            <span className="kpi-label">Annual Run Rate (ARR)</span>
            <div className="kpi-value">${overview.total_arr.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
            <span className="kpi-subtext">MRR normalized x 12</span>
          </div>
          <div className="kpi-card">
            <span className="kpi-label">Gross Margin</span>
            <div className="kpi-value text-success">{overview.finops.gross_margin_percentage}%</div>
            <span className="kpi-subtext">Revenue less direct cloud/AI costs</span>
          </div>
          <div className="kpi-card">
            <span className="kpi-label">Customer Churn Rate</span>
            <div className="kpi-value">{overview.retention.customer_churn_rate}%</div>
            <span className="kpi-subtext">Monthly logo retention</span>
          </div>
          <div className="kpi-card">
            <span className="kpi-label">Net Revenue Retention</span>
            <div className="kpi-value text-accent">{overview.retention.net_revenue_retention}%</div>
            <span className="kpi-subtext">GRR: {overview.retention.gross_revenue_retention}%</span>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="finance-tabs">
        <button
          className={`fin-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <BarChart3 size={16} /> Revenue & Unit Economics
        </button>
        <button
          className={`fin-tab-btn ${activeTab === 'transactions' ? 'active' : ''}`}
          onClick={() => setActiveTab('transactions')}
        >
          <CreditCard size={16} /> Transactions Ledger ({transactions.length})
        </button>
        <button
          className={`fin-tab-btn ${activeTab === 'finops' ? 'active' : ''}`}
          onClick={() => setActiveTab('finops')}
        >
          <PieChart size={16} /> FinOps & Cloud Budgets ({budgets.length})
        </button>
        <button
          className={`fin-tab-btn ${activeTab === 'forecasts' ? 'active' : ''}`}
          onClick={() => setActiveTab('forecasts')}
        >
          <TrendingUp size={16} /> Strategic Forecasts ({forecasts.length})
        </button>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && overview && (
        <div className="fin-tab-content">
          <div className="finance-cards-grid">
            {/* MRR Breakdown Card */}
            <div className="finance-card">
              <h3 className="card-title">MRR Movements Breakdown</h3>
              <div className="mrr-movements-list">
                <div className="mrr-row">
                  <span>New Customer MRR</span>
                  <strong className="text-success">+${overview.mrr_breakdown.new_mrr.toFixed(2)}</strong>
                </div>
                <div className="mrr-row">
                  <span>Expansion MRR (Upgrades)</span>
                  <strong className="text-success">+${overview.mrr_breakdown.expansion_mrr.toFixed(2)}</strong>
                </div>
                <div className="mrr-row">
                  <span>Contraction MRR</span>
                  <strong className="text-warning">-${overview.mrr_breakdown.contraction_mrr.toFixed(2)}</strong>
                </div>
                <div className="mrr-row">
                  <span>Churned MRR (Cancellations)</span>
                  <strong className="text-danger">-${overview.mrr_breakdown.churned_mrr.toFixed(2)}</strong>
                </div>
                <div className="mrr-divider" />
                <div className="mrr-row total-row">
                  <span>Net New MRR Contribution</span>
                  <strong className="text-accent">+${overview.mrr_breakdown.net_new_mrr.toFixed(2)}</strong>
                </div>
              </div>
            </div>

            {/* Unit Economics Card */}
            <div className="finance-card">
              <h3 className="card-title">SaaS Unit Economics</h3>
              <div className="unit-economics-grid">
                <div className="ue-item">
                  <span className="ue-label">ARPU (Average Revenue / User)</span>
                  <div className="ue-val">${overview.unit_economics.arpu.toFixed(2)}</div>
                  <span className="ue-sub">Per tenant monthly blended</span>
                </div>
                <div className="ue-item">
                  <span className="ue-label">Customer Lifetime Value (LTV)</span>
                  <div className="ue-val">${overview.unit_economics.ltv.toFixed(2)}</div>
                  <span className="ue-sub">Based on current churn profile</span>
                </div>
                <div className="ue-item">
                  <span className="ue-label">LTV / CAC Ratio</span>
                  <div className="ue-val text-success">{overview.unit_economics.ltv_to_cac_ratio}x</div>
                  <span className="ue-sub">Benchmark: &gt; 3.0x Healthy</span>
                </div>
                <div className="ue-item">
                  <span className="ue-label">CAC Payback Period</span>
                  <div className="ue-val">{overview.unit_economics.cac_payback_months} mos</div>
                  <span className="ue-sub">Recovery at gross margin</span>
                </div>
              </div>
            </div>

            {/* FinOps Direct Costs Card */}
            <div className="finance-card">
              <h3 className="card-title">FinOps Direct Cost Attribution</h3>
              <div className="finops-cost-breakdown">
                <div className="cost-row">
                  <span>Cloud Infrastructure (AWS EKS & APIs)</span>
                  <strong>${overview.finops.cloud_infrastructure_cost.toFixed(2)}</strong>
                </div>
                <div className="cost-row">
                  <span>AI Inference (Copilot Tokens)</span>
                  <strong>${overview.finops.ai_inference_cost.toFixed(2)}</strong>
                </div>
                <div className="cost-row">
                  <span>Database & Storage (RDS / S3)</span>
                  <strong>${overview.finops.database_and_storage_cost.toFixed(2)}</strong>
                </div>
                <div className="mrr-divider" />
                <div className="cost-row total-row">
                  <span>Total Cost of Goods Sold (COGS)</span>
                  <strong>${overview.finops.total_direct_costs.toFixed(2)}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: TRANSACTIONS LEDGER */}
      {activeTab === 'transactions' && (
        <div className="fin-tab-content">
          <div className="tab-actions-header">
            <h3>Billing Ledger Transactions</h3>
            <button className="btn-primary" onClick={() => setShowTxModal(true)}>
              <Plus size={16} /> Record Transaction
            </button>
          </div>

          <div className="finance-table-wrapper">
            <table className="finance-table">
              <thead>
                <tr>
                  <th>Transaction ID</th>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr key={tx.id}>
                    <td><strong className="code-tag">{tx.id.slice(0, 14)}</strong></td>
                    <td><span className="badge-type">{tx.transaction_type}</span></td>
                    <td>
                      <strong className={tx.transaction_type === 'REFUND' ? 'text-danger' : 'text-success'}>
                        {tx.transaction_type === 'REFUND' ? '-' : '+'}${tx.amount.toFixed(2)} {tx.currency}
                      </strong>
                    </td>
                    <td><span className={`status-pill ${tx.status.toLowerCase()}`}>{tx.status}</span></td>
                    <td>{new Date(tx.created_at).toLocaleDateString()}</td>
                    <td>{tx.description || 'Subscription charge'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: FINOPS & BUDGETS */}
      {activeTab === 'finops' && (
        <div className="fin-tab-content">
          <div className="tab-actions-header">
            <h3>Cloud & AI Monthly Spending Budgets</h3>
            <button className="btn-primary" onClick={() => setShowBudgetModal(true)}>
              <Plus size={16} /> Set Budget Cap
            </button>
          </div>

          <div className="budgets-grid">
            {budgets.map((b) => (
              <div key={b.id} className="budget-card">
                <div className="budget-header">
                  <span className="category-tag">{b.category}</span>
                  <span className={`budget-alert-indicator ${b.is_alert_triggered ? 'triggered' : 'safe'}`}>
                    {b.is_alert_triggered ? 'THRESHOLD EXCEEDED' : 'WITHIN BUDGET'}
                  </span>
                </div>
                <div className="budget-amounts-row">
                  <div>
                    <span className="b-label">Actual Spent</span>
                    <div className="b-val">${b.actual_spent.toFixed(2)}</div>
                  </div>
                  <div>
                    <span className="b-label">Budget Limit</span>
                    <div className="b-val-limit">${b.budget_amount.toFixed(2)}</div>
                  </div>
                </div>
                <div className="progress-bar-bg">
                  <div
                    className={`progress-bar-fill ${b.is_alert_triggered ? 'danger' : 'accent'}`}
                    style={{ width: `${Math.min(100, b.spent_percentage)}%` }}
                  />
                </div>
                <div className="budget-footer">
                  <span>{b.spent_percentage.toFixed(1)}% consumed</span>
                  <span>Alert threshold: {b.alert_threshold_percentage}%</span>
                </div>
              </div>
            ))}
          </div>

          <div className="costs-subtable-section">
            <h4>Raw Infrastructure Cost Ingestion ({costs.length} records)</h4>
            <div className="finance-table-wrapper">
              <table className="finance-table">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Amount</th>
                    <th>Period</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {costs.map((c) => (
                    <tr key={c.id}>
                      <td><span className="category-tag">{c.category}</span></td>
                      <td>{c.description}</td>
                      <td><strong>${c.amount.toFixed(2)} {c.currency}</strong></td>
                      <td>{c.billing_period}</td>
                      <td>{new Date(c.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: FORECASTS */}
      {activeTab === 'forecasts' && (
        <div className="fin-tab-content">
          <div className="tab-actions-header">
            <h3>Strategic Financial Projections & Scenario Modeling</h3>
          </div>

          <div className="finance-table-wrapper">
            <table className="finance-table">
              <thead>
                <tr>
                  <th>Scenario</th>
                  <th>Target Period</th>
                  <th>Projected MRR</th>
                  <th>Projected ARR</th>
                  <th>Projected Churn</th>
                  <th>Assumptions</th>
                </tr>
              </thead>
              <tbody>
                {forecasts.map((fc) => (
                  <tr key={fc.id}>
                    <td>
                      <span className={`badge-scenario ${fc.scenario_name.toLowerCase()}`}>
                        {fc.scenario_name}
                      </span>
                    </td>
                    <td><strong>{fc.target_period}</strong></td>
                    <td>${fc.projected_mrr.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td>${fc.projected_arr.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td>{fc.projected_churn_rate}%</td>
                    <td><span className="code-tag">{fc.assumptions_json}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL: RECORD TRANSACTION */}
      {showTxModal && (
        <div className="fin-modal-overlay" onClick={() => setShowTxModal(false)}>
          <div className="fin-modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Record Ledger Transaction</h3>
              <button className="close-btn" onClick={() => setShowTxModal(false)}>×</button>
            </div>
            <form onSubmit={handleRecordTransaction} className="modal-body form-grid">
              <div className="form-group">
                <label>Transaction Type</label>
                <select
                  value={newTx.transaction_type}
                  onChange={(e) => setNewTx({ ...newTx, transaction_type: e.target.value })}
                >
                  <option value="SUBSCRIPTION_PAYMENT">Subscription Payment</option>
                  <option value="ONE_TIME">One-Time Fee / Add-on</option>
                  <option value="REFUND">Customer Refund</option>
                  <option value="CREDIT">Account Credit</option>
                </select>
              </div>
              <div className="form-group">
                <label>Amount (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={newTx.amount}
                  onChange={(e) => setNewTx({ ...newTx, amount: e.target.value })}
                />
              </div>
              <div className="form-group full-width">
                <label>Billing Description</label>
                <input
                  type="text"
                  required
                  value={newTx.description}
                  onChange={(e) => setNewTx({ ...newTx, description: e.target.value })}
                  placeholder="e.g. Enterprise Tier Q1 Renewal"
                />
              </div>
              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={() => setShowTxModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Post Transaction</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: SET BUDGET */}
      {showBudgetModal && (
        <div className="fin-modal-overlay" onClick={() => setShowBudgetModal(false)}>
          <div className="fin-modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Set Financial Spending Cap</h3>
              <button className="close-btn" onClick={() => setShowBudgetModal(false)}>×</button>
            </div>
            <form onSubmit={handleCreateBudget} className="modal-body form-grid">
              <div className="form-group">
                <label>Category</label>
                <select
                  value={newBudget.category}
                  onChange={(e) => setNewBudget({ ...newBudget, category: e.target.value })}
                >
                  <option value="CLOUD">Cloud Infrastructure</option>
                  <option value="AI">AI Inference & LLM</option>
                  <option value="DATABASE">Database & Storage</option>
                  <option value="MARKETING">Marketing & Acquisition</option>
                </select>
              </div>
              <div className="form-group">
                <label>Monthly Limit (USD)</label>
                <input
                  type="number"
                  step="10"
                  required
                  value={newBudget.budget_amount}
                  onChange={(e) => setNewBudget({ ...newBudget, budget_amount: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Alert Warning Threshold (%)</label>
                <input
                  type="number"
                  min="50"
                  max="95"
                  required
                  value={newBudget.alert_threshold_percentage}
                  onChange={(e) => setNewBudget({ ...newBudget, alert_threshold_percentage: e.target.value })}
                />
              </div>
              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={() => setShowBudgetModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Save Budget</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
