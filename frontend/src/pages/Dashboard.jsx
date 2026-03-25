import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Zap, TrendingUp, BarChart3, ShieldCheck, ArrowUpRight, Activity } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';
import DateRangePicker from '../components/DateRangePicker';

const API_URL = 'http://localhost:5000/api';

export default function Dashboard({ merchantId, searchQuery }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({ from: null, to: null });

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const id = merchantId && merchantId !== 'all' ? merchantId : 1;
        let url = `${API_URL}/merchant/${id}/dashboard`;
        const params = [];
        if (dateRange.from) params.push(`from=${dateRange.from}`);
        if (dateRange.to) params.push(`to=${dateRange.to}`);
        if (params.length > 0) url += '?' + params.join('&');
        const res = await axios.get(url);
        setData(res.data);
      } catch (err) {
        console.error('Dashboard fetch error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [merchantId, dateRange]);

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div className="grid-cols-3">
          <div className="glass-card skeleton" style={{ height: '260px' }}></div>
          <div className="glass-card skeleton span-2" style={{ height: '260px' }}></div>
        </div>
        <div className="grid-cols-3">
          <div className="glass-card skeleton span-2" style={{ height: '360px' }}></div>
          <div className="glass-card skeleton" style={{ height: '360px' }}></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '48px', color: 'var(--danger)' }}>
        <ShieldCheck size={48} style={{ margin: '0 auto 16px' }} />
        <h3>Failed to load dashboard data</h3>
        <p style={{ color: 'var(--text-muted)', marginTop: '8px' }}>{error}</p>
      </div>
    );
  }

  const { health_score, peak_hours, customer_segments, fraud_monitor, benchmarks, 
          transaction_health, repeat_analysis, category_insights, recommendations, alerts } = data || {};

  const COLORS = ['#6366f1', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#3b82f6'];

  // Build peak hour chart data
  const peakData = (peak_hours || []).map(p => ({
    hour: `${p.hour}:00`,
    txns: parseInt(p.transaction_count) || 0,
    volume: parseFloat(p.total_volume) || 0
  }));

  // Category chart data
  const categoryData = (category_insights || []).slice(0, 6).map(c => ({
    name: c.category || c.mcc || 'Unknown',
    revenue: parseFloat(c.total_revenue) || 0
  }));

  // Search filtering for recommendations
  const filteredRecommendations = searchQuery
    ? (recommendations || []).filter(rec =>
        (rec.text || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (rec.type || '').toLowerCase().includes(searchQuery.toLowerCase())
      )
    : (recommendations || []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* Date Range Picker */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <DateRangePicker dateRange={dateRange} onDateRangeChange={setDateRange} />
      </div>

      {/* Row 1: Health Score + Recommendations */}
      <div className="grid-cols-3">
        {/* Health Score */}
        <div className="glass-card">
          <div className="card-header">
            <h3 className="card-title"><Zap size={20} color="var(--warning)" /> Business Health Score</h3>
          </div>
          <div className="health-score-container">
            <div className="health-circle" style={{
              borderColor: health_score?.status === 'Good' ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'
            }}>
              <span className="health-number">{health_score?.health_score || health_score?.score || '--'}</span>
            </div>
            <span className="health-status" style={{ color: health_score?.status === 'Good' ? 'var(--success)' : 'var(--warning)' }}>
              {health_score?.status || 'Calculating'} Performance
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px', borderTop: '1px solid var(--card-border)', paddingTop: '16px' }}>
            <div>
              <p className="metric-label" style={{ marginBottom: '4px' }}>Approval Rate</p>
              <p style={{ fontWeight: '600', color: 'var(--success)' }}>{health_score?.approval_rate || transaction_health?.approval_rate || '--'}%</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <p className="metric-label" style={{ marginBottom: '4px' }}>Fraud Rate</p>
              <p style={{ fontWeight: '600', color: 'var(--danger)' }}>{health_score?.fraud_rate || '--'}%</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <p className="metric-label" style={{ marginBottom: '4px' }}>Decline Rate</p>
              <p style={{ fontWeight: '600', color: 'var(--warning)' }}>{transaction_health?.decline_rate || '--'}%</p>
            </div>
          </div>
        </div>

        {/* AI Recommendations */}
        <div className="glass-card span-2">
          <div className="card-header">
            <h3 className="card-title"><TrendingUp size={20} color="var(--primary)" /> Smart AI Recommendations</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filteredRecommendations.length > 0 ? filteredRecommendations.map((rec, idx) => (
              <div key={idx} className="list-card">
                <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
                  <div className={`icon-badge ${rec.priority === 'High' ? 'icon-badge--success' : 'icon-badge--primary'}`}
                    style={{ width: '36px', height: '36px', flexShrink: 0 }}>
                    {rec.priority === 'High' ? <TrendingUp size={18} /> : <BarChart3 size={18} />}
                  </div>
                  <div>
                    <span style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--primary)' }}>{rec.type}</span>
                    <p style={{ fontSize: '14px', color: '#fff', marginTop: '2px' }}>{rec.text}</p>
                  </div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: '16px' }}>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Impact</p>
                  <p style={{ fontSize: '16px', fontWeight: '700', color: 'var(--success)' }}>+${rec.impact || '--'}</p>
                </div>
              </div>
            )) : (
              <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                {searchQuery ? `No recommendations matching "${searchQuery}"` : 'No recommendations available'}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Row 2: Peak Hours + Customer Segments */}
      <div className="grid-cols-3">
        {/* Peak Hours Heatmap */}
        <div className="glass-card span-2" aria-label="Peak hours transaction chart">
          <div className="card-header">
            <h3 className="card-title"><Activity size={20} color="var(--info)" /> Peak Hours Heatmap</h3>
            <div>
              <span className="metric-label">{repeat_analysis?.total_customers || '--'} unique customers</span>
            </div>
          </div>
          <div style={{ height: '280px', width: '100%', marginTop: '8px' }}>
            {peakData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={peakData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="hour" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)', borderRadius: '8px', color: '#fff' }} />
                  <Bar dataKey="txns" fill="var(--primary)" radius={[4, 4, 0, 0]} name="Transactions" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No peak hour data yet</div>
            )}
          </div>
        </div>

        {/* Customer Segments */}
        <div className="glass-card">
          <div className="card-header">
            <h3 className="card-title">Customer Breakdown</h3>
          </div>
          <div style={{ height: '200px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={(customer_segments || []).filter(s => s.count > 0)}
                  cx="50%" cy="50%"
                  innerRadius={55} outerRadius={80}
                  paddingAngle={5}
                  dataKey="count" nameKey="segment"
                >
                  {(customer_segments || []).map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)', borderRadius: '8px', color: '#fff' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px' }}>
            {(customer_segments || []).map((seg, idx) => (
              <div key={idx} className="stat-row">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: COLORS[idx % COLORS.length] }}></div>
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{seg.segment}</span>
                </div>
                <span style={{ fontWeight: '600', color: '#fff', fontSize: '13px' }}>{seg.count}</span>
              </div>
            ))}
          </div>

          {/* Repeat Customer Stats */}
          <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--card-border)' }}>
            <div className="stat-row">
              <div>
                <p className="metric-label" style={{ marginBottom: '2px' }}>Repeat Rate</p>
                <p style={{ fontWeight: '700', color: parseFloat(repeat_analysis?.repeat_rate || 0) > 30 ? 'var(--success)' : 'var(--danger)' }}>
                  {repeat_analysis?.repeat_rate || '--'}%
                </p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <p className="metric-label" style={{ marginBottom: '2px' }}>New Customers</p>
                <p style={{ fontWeight: '700', color: 'var(--info)' }}>{repeat_analysis?.new_customer_rate || '--'}%</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: Competitor Benchmarks + Category Insights */}
      <div className="grid-cols-2">
        {/* Competitor Benchmarking */}
        <div className="glass-card" aria-label="Competitor benchmarking chart">
          <div className="card-header">
            <h3 className="card-title"><BarChart3 size={20} color="var(--warning)" /> Competitor Benchmarking</h3>
            {benchmarks && <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>MCC: {benchmarks.mcc}</span>}
          </div>
          {benchmarks ? (
            <>
              <div style={{ display: 'flex', gap: '24px', marginBottom: '20px' }}>
                <div style={{ flex: 1, background: 'rgba(99,102,241,0.1)', borderRadius: '12px', padding: '16px', textAlign: 'center' }}>
                  <p className="metric-label">Your Avg Ticket</p>
                  <p style={{ fontSize: '28px', fontWeight: '700', color: 'var(--primary)' }}>${parseFloat(benchmarks.merchant_ticket || 0).toFixed(0)}</p>
                </div>
                <div style={{ flex: 1, background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '16px', textAlign: 'center' }}>
                  <p className="metric-label">Industry Avg</p>
                  <p style={{ fontSize: '28px', fontWeight: '700', color: 'var(--text-muted)' }}>${parseFloat(benchmarks.industry_ticket || 0).toFixed(0)}</p>
                </div>
              </div>
              <div style={{ padding: '12px 16px', background: parseFloat(benchmarks.performance_gap || 0) >= 0 ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', borderRadius: '8px', borderLeft: `4px solid ${parseFloat(benchmarks.performance_gap || 0) >= 0 ? 'var(--success)' : 'var(--danger)'}` }}>
                <p style={{ fontSize: '14px', color: '#fff' }}>
                  <strong>Performance Gap: </strong>
                  <span style={{ color: parseFloat(benchmarks.performance_gap || 0) >= 0 ? 'var(--success)' : 'var(--danger)' }}>
                    {parseFloat(benchmarks.performance_gap || 0) >= 0 ? '+' : ''}${parseFloat(benchmarks.performance_gap || 0).toFixed(2)} vs industry
                  </span>
                </p>
              </div>
            </>
          ) : (
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', paddingTop: '40px' }}>No benchmark data available</p>
          )}
        </div>

        {/* Category Insights */}
        <div className="glass-card" aria-label="Category insights chart">
          <div className="card-header">
            <h3 className="card-title"><ArrowUpRight size={20} color="var(--success)" /> Category / MCC Insights</h3>
          </div>
          <div style={{ height: '260px', width: '100%' }}>
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryData} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                  <XAxis type="number" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
                  <YAxis dataKey="name" type="category" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} width={80} />
                  <Tooltip contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)', borderRadius: '8px', color: '#fff' }} formatter={v => [`$${parseFloat(v).toFixed(2)}`, 'Revenue']} />
                  <Bar dataKey="revenue" fill="var(--success)" radius={[0, 4, 4, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No category data yet</div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
