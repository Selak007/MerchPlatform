import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Target, PieChart as PieIcon, TrendingUp } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend, PieChart, Pie, Cell } from 'recharts';
import DateRangePicker from '../components/DateRangePicker';

const API_URL = 'http://localhost:5000/api';

export default function Revenue({ merchantId, searchQuery }) {
  const [benchmarks, setBenchmarks] = useState(null);
  const [categories, setCategories] = useState([]);
  const [pricingSignal, setPricingSignal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({ from: null, to: null });

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const id = merchantId && merchantId !== 'all' ? merchantId : 1;
        let url = `${API_URL}/merchant/${id}/dashboard`;
        const params = [];
        if (dateRange.from) params.push(`from=${dateRange.from}`);
        if (dateRange.to) params.push(`to=${dateRange.to}`);
        if (params.length > 0) url += '?' + params.join('&');
        const res = await axios.get(url);
        setBenchmarks(res.data.benchmarks);
        setCategories(res.data.category_insights || []);
        setPricingSignal(res.data.pricing_signal || null);
      } catch (err) {
        console.error('Error fetching revenue data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [merchantId, dateRange]);

  if (loading) {
    return (
      <div className="grid-cols-2">
        <div className="glass-card skeleton" style={{ height: '400px' }}></div>
        <div className="glass-card skeleton" style={{ height: '400px' }}></div>
      </div>
    );
  }

  const merchantTicket = parseFloat(benchmarks?.merchant_ticket || 0);
  const industryTicket = parseFloat(benchmarks?.industry_ticket || 0);
  const benchmarkChartData = [
    { name: 'Avg Ticket Size', You: merchantTicket, Industry: industryTicket }
  ];

  const COLORS = ['#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#3b82f6'];
  const categoryChartData = categories.filter(c => c.category || c.mcc);

  // Search filtering
  const filteredCategories = searchQuery
    ? categoryChartData.filter(c =>
        ((c.category || c.mcc || '')).toLowerCase().includes(searchQuery.toLowerCase())
      )
    : categoryChartData;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* Date Range Picker */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <DateRangePicker dateRange={dateRange} onDateRangeChange={setDateRange} />
      </div>

      {/* AI Pricing Advisor */}
      {pricingSignal && (
        <div className="glass-card">
          <div className="card-header">
            <h3 className="card-title"><TrendingUp size={20} color="var(--success)" /> AI Pricing Advisor</h3>
          </div>
          <div style={{ display: 'flex', gap: '24px' }}>
            <div style={{ flex: 1, background: 'rgba(16,185,129,0.08)', borderRadius: '12px', padding: '20px', textAlign: 'center' }}>
              <p className="metric-label">Avg Transaction Amount</p>
              <p style={{ fontSize: '32px', fontWeight: '700', color: 'var(--success)' }}>${parseFloat(pricingSignal.avg_ticket || 0).toFixed(2)}</p>
            </div>
            <div style={{ flex: 1, background: 'rgba(239,68,68,0.08)', borderRadius: '12px', padding: '20px', textAlign: 'center' }}>
              <p className="metric-label">Price Variance (StdDev)</p>
              <p style={{ fontSize: '32px', fontWeight: '700', color: 'var(--danger)' }}>${parseFloat(pricingSignal.price_variance || 0).toFixed(2)}</p>
            </div>
            <div style={{ flex: 2, background: 'rgba(99,102,241,0.08)', borderRadius: '12px', padding: '20px' }}>
              <p className="metric-label">Pricing Recommendation</p>
              <p style={{ fontSize: '15px', color: 'var(--text-heading)', marginTop: '8px' }}>
                {merchantTicket < industryTicket
                  ? `Your avg ticket ($${merchantTicket.toFixed(0)}) is below industry avg ($${industryTicket.toFixed(0)}). Recommend a 5–10% price increase on high-demand items.`
                  : `Your pricing is competitive. High variance ($${parseFloat(pricingSignal.price_variance || 0).toFixed(2)}) suggests opportunity to standardize premium tiers.`
                }
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid-cols-2">
        {/* Competitor Benchmarking */}
        <div className="glass-card">
          <div className="card-header">
            <h3 className="card-title"><Target size={20} color="var(--primary)" /> Competitor Benchmarking</h3>
            {benchmarks && <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>MCC {benchmarks.mcc}</span>}
          </div>
          {benchmarkChartData[0].You > 0 ? (
            <>
              <div style={{ height: '240px', width: '100%', marginTop: '20px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={benchmarkChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--grid-stroke)" vertical={false} />
                    <XAxis dataKey="name" stroke="var(--text-muted)" tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--text-muted)" tickLine={false} axisLine={false} tickFormatter={v => `$${v}`} />
                    <Tooltip contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)', borderRadius: '8px', color: 'var(--text-heading)' }} cursor={{ fill: 'var(--grid-stroke)' }} />
                    <Legend />
                    <Bar dataKey="You" fill="var(--primary)" radius={[4, 4, 0, 0]} barSize={50} />
                    <Bar dataKey="Industry" fill="rgba(148,163,184,0.4)" radius={[4, 4, 0, 0]} barSize={50} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div style={{ marginTop: '16px', padding: '12px 16px', background: parseFloat(benchmarks?.performance_gap || 0) >= 0 ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', borderRadius: '8px', borderLeft: `4px solid ${parseFloat(benchmarks?.performance_gap || 0) >= 0 ? 'var(--success)' : 'var(--danger)'}` }}>
                <p style={{ fontSize: '14px', color: 'var(--text-heading)' }}>
                  <strong>Performance Gap: </strong>
                  <span style={{ color: parseFloat(benchmarks?.performance_gap || 0) >= 0 ? 'var(--success)' : 'var(--danger)' }}>
                    {parseFloat(benchmarks?.performance_gap || 0) >= 0 ? '+' : ''}${parseFloat(benchmarks?.performance_gap || 0).toFixed(2)} vs industry
                  </span>
                </p>
              </div>
            </>
          ) : <p style={{ color: 'var(--text-muted)', textAlign: 'center', paddingTop: '48px' }}>No benchmark data</p>}
        </div>

        {/* Category / Product Insights */}
        <div className="glass-card">
          <div className="card-header">
            <h3 className="card-title"><PieIcon size={20} color="var(--warning)" /> Category Insights</h3>
          </div>
          {filteredCategories.length > 0 ? (
            <>
              <div style={{ height: '260px', width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={filteredCategories} cx="50%" cy="50%" innerRadius={70} outerRadius={100} paddingAngle={5}
                      dataKey="total_revenue" nameKey="category">
                      {filteredCategories.map((_, index) => (
                        <Cell key={index} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)', borderRadius: '8px', color: 'var(--text-heading)' }}
                      formatter={v => [`$${parseFloat(v).toFixed(2)}`, 'Revenue']} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {filteredCategories.slice(0, 5).map((c, i) => (
                  <div key={i} className="stat-row">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: COLORS[i % COLORS.length] }}></div>
                      <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{c.category || c.mcc}</span>
                    </div>
                    <span style={{ fontWeight: '600', color: 'var(--text-heading)', fontSize: '13px' }}>${parseFloat(c.total_revenue || 0).toFixed(0)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : <p style={{ color: 'var(--text-muted)', textAlign: 'center', paddingTop: '48px' }}>{searchQuery ? `No categories matching "${searchQuery}"` : 'No category data yet for this merchant.'}</p>}
        </div>
      </div>
    </div>
  );
}
