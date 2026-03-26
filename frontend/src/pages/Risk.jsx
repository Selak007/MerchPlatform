import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ShieldAlert, AlertTriangle, AlertCircle, ShieldCheck, Activity, TrendingDown } from 'lucide-react';
import { ResponsiveContainer, RadialBarChart, RadialBar, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, Cell } from 'recharts';

const API_URL = 'http://localhost:5000/api';

const RISK_COLORS = {
  critical: { bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.4)', color: '#ef4444' },
  warning: { bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.4)', color: '#f59e0b' },
  info: { bg: 'rgba(59,130,246,0.15)', border: 'rgba(59,130,246,0.4)', color: '#3b82f6' }
};

const FRAUD_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e'];

export default function Risk({ merchantId, searchQuery }) {
  const [fraudData, setFraudData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const id = merchantId && merchantId !== 'all' ? merchantId : 1;
        const res = await axios.get(`${API_URL}/merchant/${id}/dashboard`);
        setFraudData(res.data.fraud_monitor || []);
        setAlerts(res.data.alerts || []);
        setHealth(res.data.health_score || null);
      } catch (err) {
        console.error('Error fetching risk data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [merchantId]);

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div className="grid-cols-3">
          {[0, 1, 2].map(i => <div key={i} className="glass-card skeleton" style={{ height: '140px' }}></div>)}
        </div>
        <div className="grid-cols-2">
          <div className="glass-card skeleton" style={{ height: '420px' }}></div>
          <div className="glass-card skeleton" style={{ height: '420px' }}></div>
        </div>
      </div>
    );
  }

  const fraudRate = parseFloat(health?.fraud_rate || 0);
  const approvalRate = parseFloat(health?.approval_rate || health?.approvalRate || 0);
  const declineRate = parseFloat(100 - approvalRate).toFixed(2);
  const riskLevel = fraudRate > 3 ? 'High' : fraudRate > 1 ? 'Medium' : 'Low';
  const riskColor = fraudRate > 3 ? '#ef4444' : fraudRate > 1 ? '#f59e0b' : '#10b981';

  const validFraud = fraudData.filter(f => f.fraud_type);
  const totalFraudCases = validFraud.reduce((s, f) => s + (parseInt(f.count) || 0), 0);

  // Format fraud type labels
  const chartData = validFraud.map(f => ({
    ...f,
    label: f.fraud_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    count: parseInt(f.count) || 0,
    risk: parseFloat(f.avg_risk_score || f.avg_risk || 0).toFixed(0)
  }));

  // Search filtering
  const filteredChartData = searchQuery
    ? chartData.filter(row =>
        row.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : chartData;

  const filteredAlerts = searchQuery
    ? alerts.filter(alert =>
        (alert.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (alert.message || '').toLowerCase().includes(searchQuery.toLowerCase())
      )
    : alerts;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* Risk KPI Cards */}
      <div className="grid-cols-3">
        <div className="glass-card" style={{ border: `1px solid ${riskColor}44` }}>
          <div className="stat-row" style={{ alignItems: 'flex-start' }}>
            <div>
              <p className="metric-label">Fraud Rate</p>
              <p style={{ fontSize: '40px', fontWeight: '800', color: riskColor, lineHeight: 1.1 }}>{fraudRate}%</p>
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: '6px', marginTop: '8px',
                padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '700',
                background: `${riskColor}22`, color: riskColor
              }}>
                {riskLevel === 'High' ? <AlertTriangle size={12} /> : riskLevel === 'Medium' ? <AlertCircle size={12} /> : <ShieldCheck size={12} />}
                {riskLevel} Risk
              </div>
            </div>
            <div className="icon-badge" style={{ padding: '12px', borderRadius: '12px', background: `${riskColor}15` }}>
              <ShieldAlert size={28} color={riskColor} />
            </div>
          </div>
        </div>

        <div className="glass-card">
          <div className="stat-row" style={{ alignItems: 'flex-start' }}>
            <div>
              <p className="metric-label">Approval Rate</p>
              <p style={{ fontSize: '40px', fontWeight: '800', color: '#10b981', lineHeight: 1.1 }}>{approvalRate}%</p>
              <div style={{ marginTop: '8px', height: '6px', background: 'var(--bar-track)', borderRadius: '3px', overflow: 'hidden', width: '120px' }}>
                <div style={{ width: `${approvalRate}%`, height: '100%', background: '#10b981', borderRadius: '3px' }}></div>
              </div>
            </div>
            <div className="icon-badge" style={{ padding: '12px', borderRadius: '12px', background: 'rgba(16,185,129,0.15)' }}>
              <ShieldCheck size={28} color="#10b981" />
            </div>
          </div>
        </div>

        <div className="glass-card">
          <div className="stat-row" style={{ alignItems: 'flex-start' }}>
            <div>
              <p className="metric-label">Total Fraud Cases</p>
              <p style={{ fontSize: '40px', fontWeight: '800', color: 'var(--text-heading)', lineHeight: 1.1 }}>{totalFraudCases}</p>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px' }}>across {validFraud.length} fraud types</p>
            </div>
            <div className="icon-badge" style={{ padding: '12px', borderRadius: '12px', background: 'rgba(99,102,241,0.15)' }}>
              <Activity size={28} color="var(--primary)" />
            </div>
          </div>
        </div>
      </div>

      {/* Fraud Breakdown + Alerts */}
      <div className="grid-cols-2">
        {/* Fraud Type Breakdown */}
        <div className="glass-card" aria-label="Fraud type breakdown chart">
          <div className="card-header">
            <h3 className="card-title"><ShieldAlert size={18} color="var(--danger)" /> Fraud Type Breakdown</h3>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{totalFraudCases} total cases detected</span>
          </div>

          {filteredChartData.length > 0 ? (
            <>
              {/* Horizontal bar chart */}
              <div style={{ height: '240px', marginTop: '8px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={filteredChartData} layout="vertical" margin={{ left: 0, right: 40, top: 5, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-stroke)" horizontal={false} />
                    <XAxis type="number" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis dataKey="label" type="category" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} width={140} />
                    <Tooltip
                      contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)', borderRadius: '8px', color: 'var(--text-heading)' }}
                      formatter={(value, name) => [value, 'Cases']}
                      cursor={{ fill: 'var(--grid-stroke)' }}
                    />
                    <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={20}>
                      {filteredChartData.map((_, idx) => (
                        <Cell key={idx} fill={FRAUD_COLORS[idx % FRAUD_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Detailed list */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '16px' }}>
                {filteredChartData.map((row, i) => (
                  <div key={i} className="list-card" style={{
                    border: `1px solid ${FRAUD_COLORS[i % FRAUD_COLORS.length]}33`
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: FRAUD_COLORS[i % FRAUD_COLORS.length], flexShrink: 0 }}></div>
                      <span style={{ fontSize: '14px', color: 'var(--text-heading)' }}>{row.label}</span>
                    </div>
                    <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                      <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{row.count} cases</span>
                      <span style={{
                        padding: '2px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: '700',
                        background: parseInt(row.risk) > 85 ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)',
                        color: parseInt(row.risk) > 85 ? '#ef4444' : '#f59e0b'
                      }}>
                        Risk {row.risk}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
              <ShieldCheck size={52} style={{ margin: '0 auto 12px', color: '#10b981', display: 'block' }} />
              <p style={{ fontSize: '16px', color: 'var(--text-heading)' }}>{searchQuery ? `No fraud types matching "${searchQuery}"` : 'No Fraud Detected'}</p>
              <p style={{ fontSize: '13px', marginTop: '4px' }}>{searchQuery ? '' : 'This merchant has a clean transaction history.'}</p>
            </div>
          )}
        </div>

        {/* Smart Alerts */}
        <div className="glass-card">
          <div className="card-header">
            <h3 className="card-title"><AlertCircle size={18} color="var(--warning)" /> Smart Alerts System</h3>
            <span style={{
              padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '700',
              background: alerts.some(a => a.type === 'critical') ? 'rgba(239,68,68,0.15)' : 'rgba(16,185,129,0.15)',
              color: alerts.some(a => a.type === 'critical') ? '#ef4444' : '#10b981'
            }}>
              {alerts.filter(a => a.type === 'critical').length} Critical
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
            {filteredAlerts.length > 0 ? filteredAlerts.map((alert, idx) => {
              const c = RISK_COLORS[alert.type] || RISK_COLORS.info;
              return (
                <div key={idx} style={{
                  display: 'flex', gap: '16px', alignItems: 'flex-start', padding: '16px',
                  borderRadius: '12px', background: c.bg, border: `1px solid ${c.border}`
                }}>
                  <div style={{ padding: '8px', borderRadius: '8px', background: `${c.color}22`, color: c.color, flexShrink: 0 }}>
                    {alert.type === 'critical' ? <AlertTriangle size={20} /> : alert.type === 'warning' ? <TrendingDown size={20} /> : <ShieldCheck size={20} />}
                  </div>
                  <div>
                    <h4 style={{ fontSize: '15px', color: 'var(--text-heading)', marginBottom: '4px', fontWeight: '600' }}>{alert.title}</h4>
                    <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.5 }}>{alert.message}</p>
                  </div>
                  <div style={{ marginLeft: 'auto', flexShrink: 0 }}>
                    <span style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', color: c.color, letterSpacing: '0.05em' }}>
                      {alert.type}
                    </span>
                  </div>
                </div>
              );
            }) : (
              <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                {searchQuery ? `No alerts matching "${searchQuery}"` : 'No alerts'}
              </div>
            )}
          </div>

          {/* Risk Score Summary */}
          <div style={{ marginTop: '24px', padding: '20px', borderRadius: '12px', background: 'var(--bg-subtle)', border: '1px solid var(--card-border)' }}>
            <h4 style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Risk Level Summary</h4>
            {[
              { label: 'Fraud Rate', value: fraudRate, max: 10, color: riskColor },
              { label: 'Approval Rate', value: approvalRate, max: 100, color: '#10b981' },
              { label: 'Decline Rate', value: parseFloat(declineRate), max: 100, color: '#f59e0b' }
            ].map((item, i) => (
              <div key={i} style={{ marginBottom: i < 2 ? '14px' : 0 }}>
                <div className="stat-row" style={{ marginBottom: '6px' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{item.label}</span>
                  <span style={{ fontSize: '13px', fontWeight: '700', color: item.color }}>{item.value}%</span>
                </div>
                <div style={{ height: '6px', background: 'var(--bg-overlay)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{
                    width: `${Math.min(100, (item.value / item.max) * 100)}%`,
                    height: '100%', background: item.color, borderRadius: '3px',
                    transition: 'width 1s ease'
                  }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
}
