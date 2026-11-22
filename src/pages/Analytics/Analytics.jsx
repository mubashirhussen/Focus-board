import React, { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Download,
  Calendar,
  Sparkles,
  Layers,
  BarChart2,
  PieChart,
} from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import { useAuth } from '../../context/AuthContext';
import { analyticsApi } from '../../services/analyticsApi';
import './Analytics.css';

export function Analytics() {
  const { tasks, stats } = useTasks();
  const { isAuthenticated } = useAuth();

  const [dateRange, setDateRange] = useState(7); // 7, 30, 90 days
  const [trends, setTrends] = useState([]);
  const [insights, setInsights] = useState([]);
  const [isExporting, setIsExporting] = useState(false);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);

  // Compute local or remote analytics
  useEffect(() => {
    if (isAuthenticated) {
      setLoadingAnalytics(true);
      Promise.all([
        analyticsApi.getTrends(dateRange).catch(() => []),
        analyticsApi.getInsights().catch(() => ({ insights: [] })),
      ])
        .then(([trendData, insightData]) => {
          setTrends(trendData || []);
          setInsights(insightData.insights || []);
        })
        .finally(() => setLoadingAnalytics(false));
    } else {
      // Local computation for guest/offline mode
      generateLocalTrends(dateRange);
    }
  }, [isAuthenticated, dateRange, tasks]);

  // Generate trend bars for local data
  const generateLocalTrends = (days) => {
    const list = [];
    const today = new Date();
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date();
      d.setDate(today.getDate() - i);
      const dStr = d.toISOString().split('T')[0];

      // Count tasks matching this date
      const createdCount = tasks.filter((t) => (t.createdAt || '').startsWith(dStr)).length;
      const completedCount = tasks.filter(
        (t) => (t.status || '').toLowerCase() === 'completed' && (t.updatedAt || '').startsWith(dStr)
      ).length;

      list.push({
        date: dStr,
        dayLabel: d.toLocaleDateString('en-US', { weekday: 'short', month: 'numeric', day: 'numeric' }),
        created: createdCount,
        completed: completedCount,
      });
    }
    setTrends(list);

    // Local insights
    const total = tasks.length;
    const completed = stats.completed;
    const rate = stats.completionRate;
    const localInsights = [];

    if (total === 0) {
      localInsights.push({
        type: 'info',
        title: 'Ready for Launch',
        message: 'Add tasks to start unlocking your personalized productivity insights.',
      });
    } else {
      if (rate >= 70) {
        localInsights.push({
          type: 'success',
          title: 'High Velocity',
          message: `Great momentum! You have completed ${rate}% of all assigned tasks.`,
        });
      } else {
        localInsights.push({
          type: 'warning',
          title: 'Task Pacing',
          message: `${stats.pending} task(s) remain pending. Focus on high priority items to accelerate progress.`,
        });
      }

      if (stats.overdue > 0) {
        localInsights.push({
          type: 'warning',
          title: 'Overdue Deadlines',
          message: `You have ${stats.overdue} task(s) past due. Reschedule or prioritize to stay on track.`,
        });
      } else {
        localInsights.push({
          type: 'success',
          title: 'Clean Slate',
          message: 'Zero overdue tasks. All deadlines are within schedule.',
        });
      }
    }
    setInsights(localInsights);
  };

  // Distributions
  const statusDistribution = useMemo(() => {
    const total = tasks.length || 1;
    return [
      { name: 'Completed', count: stats.completed, color: '#10B981', pct: Math.round((stats.completed / total) * 100) },
      { name: 'In Progress', count: stats.inProgress, color: '#F59E0B', pct: Math.round((stats.inProgress / total) * 100) },
      { name: 'Todo', count: stats.todo, color: '#64748B', pct: Math.round((stats.todo / total) * 100) },
    ];
  }, [tasks, stats]);

  const priorityDistribution = useMemo(() => {
    const total = tasks.length || 1;
    const counts = { High: 0, Medium: 0, Low: 0 };
    tasks.forEach((t) => {
      const p = t.priority || 'Medium';
      if (counts[p] !== undefined) counts[p]++;
    });
    return [
      { name: 'High', count: counts.High, color: '#EF4444', pct: Math.round((counts.High / total) * 100) },
      { name: 'Medium', count: counts.Medium, color: '#3B82F6', pct: Math.round((counts.Medium / total) * 100) },
      { name: 'Low', count: counts.Low, color: '#10B981', pct: Math.round((counts.Low / total) * 100) },
    ];
  }, [tasks]);

  const categoryDistribution = useMemo(() => {
    const total = tasks.length || 1;
    const catCounts = {};
    tasks.forEach((t) => {
      const cat = t.category || 'General';
      catCounts[cat] = (catCounts[cat] || 0) + 1;
    });
    return Object.entries(catCounts).map(([cat, count]) => ({
      name: cat,
      count,
      pct: Math.round((count / total) * 100),
    }));
  }, [tasks]);

  // Export CSV handler
  const handleExportCsv = async () => {
    setIsExporting(true);
    try {
      if (isAuthenticated) {
        await analyticsApi.downloadCsv();
      } else {
        // Local CSV download
        let csvContent = 'data:text/csv;charset=utf-8,\ufeff';
        csvContent += 'Task ID,Title,Category,Status,Priority,Due Date,Created At\n';
        tasks.forEach((t) => {
          const safeTitle = (t.title || '').replace(/"/g, '""');
          const safeTitleEscaped = safeTitle.match(/^[=+\-@]/) ? `'${safeTitle}` : safeTitle;
          csvContent += `"${t.id}","${safeTitleEscaped}","${t.category}","${t.status}","${t.priority}","${t.dueDate || 'None'}","${t.createdAt}"\n`;
        });
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', `focusboard_local_tasks_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err) {
      alert(`Export error: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  const maxTrendVal = Math.max(...trends.map((t) => Math.max(t.completed || 0, t.created || 0)), 3);

  return (
    <div className="analytics-page">
      {/* Top Header & Toolbar */}
      <div className="analytics-header">
        <div className="analytics-header-titles">
          <h1 className="analytics-title">Productivity & Analytics</h1>
          <p className="analytics-subtitle">Real-time velocity metrics, task distributions, and performance insights.</p>
        </div>

        <div className="analytics-toolbar">
          {/* Time range selector */}
          <div className="range-selector" role="group" aria-label="Select trend timeframe">
            <button
              type="button"
              className={`range-btn ${dateRange === 7 ? 'active' : ''}`}
              onClick={() => setDateRange(7)}
            >
              7 Days
            </button>
            <button
              type="button"
              className={`range-btn ${dateRange === 30 ? 'active' : ''}`}
              onClick={() => setDateRange(30)}
            >
              30 Days
            </button>
            <button
              type="button"
              className={`range-btn ${dateRange === 90 ? 'active' : ''}`}
              onClick={() => setDateRange(90)}
            >
              90 Days
            </button>
          </div>

          {/* Export CSV Action */}
          <button
            type="button"
            className="export-csv-btn"
            onClick={handleExportCsv}
            disabled={isExporting || tasks.length === 0}
            title="Download CSV export with security sanitization"
          >
            <Download size={15} />
            <span>{isExporting ? 'Exporting...' : 'Export CSV'}</span>
          </button>
        </div>
      </div>

      {/* KPI Stat Cards Grid */}
      <div className="analytics-kpi-grid">
        <div className="analytics-kpi-card">
          <div className="kpi-icon-wrapper total">
            <Layers size={20} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">TOTAL ASSIGNMENTS</span>
            <span className="kpi-value">{tasks.length}</span>
          </div>
        </div>

        <div className="analytics-kpi-card">
          <div className="kpi-icon-wrapper completed">
            <CheckCircle2 size={20} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">COMPLETED</span>
            <span className="kpi-value">{stats.completed}</span>
          </div>
        </div>

        <div className="analytics-kpi-card">
          <div className="kpi-icon-wrapper rate">
            <TrendingUp size={20} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">COMPLETION VELOCITY</span>
            <span className="kpi-value">{stats.completionRate}%</span>
          </div>
        </div>

        <div className="analytics-kpi-card">
          <div className={`kpi-icon-wrapper ${stats.overdue > 0 ? 'overdue' : 'neutral'}`}>
            <AlertTriangle size={20} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">OVERDUE DEADLINES</span>
            <span className="kpi-value">{stats.overdue}</span>
          </div>
        </div>
      </div>

      {/* Main Trends & Distribution Grid */}
      <div className="analytics-charts-grid">
        {/* Completion & Creation Trends Chart */}
        <div className="chart-card trends-card">
          <div className="chart-card-header">
            <div className="chart-title-group">
              <BarChart2 size={18} className="chart-title-icon" />
              <h2 className="chart-card-title">Completion Trends (Last {dateRange} Days)</h2>
            </div>
            <div className="chart-legend">
              <span className="legend-item"><span className="legend-dot completed" /> Completed</span>
              <span className="legend-item"><span className="legend-dot created" /> Created</span>
            </div>
          </div>

          <div className="trend-bars-container">
            {trends.length === 0 ? (
              <div className="empty-trends">No activity recorded for this timeframe.</div>
            ) : (
              trends.map((t, idx) => {
                const compHeight = Math.max(4, Math.round(((t.completed || 0) / maxTrendVal) * 120));
                const crtHeight = Math.max(4, Math.round(((t.created || 0) / maxTrendVal) * 120));
                const label = t.dayLabel || t.date.slice(5);

                return (
                  <div key={idx} className="trend-column" title={`${t.date}: ${t.completed} completed, ${t.created} created`}>
                    <div className="bars-pair">
                      <div className="bar bar-completed" style={{ height: `${compHeight}px` }} />
                      <div className="bar bar-created" style={{ height: `${crtHeight}px` }} />
                    </div>
                    <span className="trend-date-label">{label}</span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* AI Productivity Insights */}
        <div className="chart-card insights-card">
          <div className="chart-card-header">
            <div className="chart-title-group">
              <Sparkles size={18} className="chart-title-icon" />
              <h2 className="chart-card-title">Productivity Insights</h2>
            </div>
          </div>

          <div className="insights-list">
            {insights.length === 0 ? (
              <p className="no-insights">Keep creating and finishing tasks to receive real-time productivity assessments.</p>
            ) : (
              insights.map((ins, idx) => (
                <div key={idx} className={`insight-item ${ins.type || 'info'}`}>
                  <div className="insight-badge">{ins.type?.toUpperCase() || 'INFO'}</div>
                  <h4 className="insight-title">{ins.title}</h4>
                  <p className="insight-message">{ins.message}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Breakdown Distributions */}
      <div className="distributions-grid">
        {/* Status Breakdown */}
        <div className="distribution-card">
          <h3 className="distribution-title">Tasks by Status</h3>
          <div className="dist-items">
            {statusDistribution.map((item) => (
              <div key={item.name} className="dist-row">
                <div className="dist-info">
                  <span className="dist-name">{item.name}</span>
                  <span className="dist-count">{item.count} ({item.pct}%)</span>
                </div>
                <div className="dist-progress-track">
                  <div className="dist-progress-bar" style={{ width: `${item.pct}%`, backgroundColor: item.color }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Priority Breakdown */}
        <div className="distribution-card">
          <h3 className="distribution-title">Tasks by Priority</h3>
          <div className="dist-items">
            {priorityDistribution.map((item) => (
              <div key={item.name} className="dist-row">
                <div className="dist-info">
                  <span className="dist-name">{item.name} Priority</span>
                  <span className="dist-count">{item.count} ({item.pct}%)</span>
                </div>
                <div className="dist-progress-track">
                  <div className="dist-progress-bar" style={{ width: `${item.pct}%`, backgroundColor: item.color }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="distribution-card">
          <h3 className="distribution-title">Tasks by Category</h3>
          <div className="dist-items">
            {categoryDistribution.map((item) => (
              <div key={item.name} className="dist-row">
                <div className="dist-info">
                  <span className="dist-name">{item.name}</span>
                  <span className="dist-count">{item.count} ({item.pct}%)</span>
                </div>
                <div className="dist-progress-track">
                  <div className="dist-progress-bar" style={{ width: `${item.pct}%`, backgroundColor: '#4F46E5' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
