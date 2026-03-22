import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Users, UserPlus, UserCheck, Activity } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

const API_URL = 'http://localhost:5000/api';

export default function Customers({ merchantId }) {
  const [segments, setSegments] = useState([]);
  const [repeatData, setRepeatData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const id = merchantId && merchantId !== 'all' ? merchantId : 1;
        const res = await axios.get(`${API_URL}/merchant/${id}/dashboard`);
        setSegments(res.data.customer_segments || []);
        setRepeatData(res.data.repeat_analysis || null);
      } catch (err) {
        console.error('Error fetching customer data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [merchantId]);

  if (loading) {
    return (
      <div className="grid-cols-3">
        <div className="glass-card skeleton" style={{ height: '200px' }}></div>
        <div className="glass-card skeleton" style={{ height: '200px' }}></div>
        <div className="glass-card skeleton" style={{ height: '200px' }}></div>
      </div>
    );
  }

  const totalUsers = parseInt(repeatData?.total_customers || 0);
  const repeatRate = parseFloat(repeatData?.repeat_rate || 0);
  const newRate = parseFloat(repeatData?.new_customer_rate || 0);

  const activityData = [
    { day: 'Mon', active: Math.round(totalUsers * 0.12) }, { day: 'Tue', active: Math.round(totalUsers * 0.15) },
    { day: 'Wed', active: Math.round(totalUsers * 0.18) }, { day: 'Thu', active: Math.round(totalUsers * 0.17) },
    { day: 'Fri', active: Math.round(totalUsers * 0.22) }, { day: 'Sat', active: Math.round(totalUsers * 0.31) },
    { day: 'Sun', active: Math.round(totalUsers * 0.28) }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="grid-cols-3">
        <div className="glass-card">
          <div className="card-header">
            <h3 className="card-title">Total Customers</h3>
            <div style={{ padding: '8px', background: 'rgba(99,102,241,0.15)', borderRadius: '8px', color: 'var(--primary)' }}>
              <Users size={20} />
            </div>
          </div>
          <div className="metric-value">{totalUsers.toLocaleString()}</div>
          <p className="metric-label" style={{ margin: 0 }}>Unique customers (this merchant)</p>
        </div>

        <div className="glass-card">
          <div className="card-header">
            <h3 className="card-title">Repeat Rate (Loyalty)</h3>
            <div style={{ padding: '8px', background: 'rgba(16,185,129,0.15)', borderRadius: '8px', color: 'var(--success)' }}>
              <UserCheck size={20} />
            </div>
          </div>
          <div className="metric-value">{repeatRate}%</div>
          <div className={`trend-badge ${repeatRate > 40 ? 'trend-up' : 'trend-down'}`} style={{ marginTop: '8px' }}>
            {repeatRate > 40 ? 'Healthy retention' : 'Low retention risk'}
          </div>
        </div>

        <div className="glass-card">
          <div className="card-header">
            <h3 className="card-title">First-Time Buyers</h3>
            <div style={{ padding: '8px', background: 'rgba(239,68,68,0.15)', borderRadius: '8px', color: 'var(--danger)' }}>
              <UserPlus size={20} />
            </div>
          </div>
          <div className="metric-value">{newRate}%</div>
          <p className="metric-label" style={{ margin: 0 }}>Potential to convert to repeat</p>
        </div>
      </div>

      <div className="grid-cols-2">
        <div className="glass-card">
          <div className="card-header"><h3 className="card-title">Customer Segments</h3></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
            {segments.map((seg, idx) => (
              <div key={idx} style={{
                background: 'rgba(255,255,255,0.03)', border: '1px solid var(--card-border)',
                borderRadius: '12px', padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
              }}>
                <div>
                  <h4 style={{ fontSize: '15px', color: '#fff', marginBottom: '4px' }}>{seg.segment}</h4>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{seg.count.toLocaleString()} Users</p>
                </div>
                <div style={{
                  padding: '6px 14px', borderRadius: '20px',
                  background: idx === 0 ? 'rgba(99,102,241,0.15)' : idx === 1 ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
                  color: idx === 0 ? 'var(--primary)' : idx === 1 ? 'var(--success)' : 'var(--warning)',
                  fontWeight: '700', fontSize: '14px'
                }}>
                  {seg.count > 0 ? ((seg.count / (segments.reduce((a,s)=>a+s.count,0) || 1)) * 100).toFixed(0) + '%' : '0%'}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card">
          <div className="card-header">
            <h3 className="card-title"><Activity size={20} color="var(--info)" /> Estimated Weekly Activity</h3>
          </div>
          <div style={{ height: '300px', width: '100%', marginTop: '20px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={activityData}>
                <defs>
                  <linearGradient id="colorActive" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--info)" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="var(--info)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="day" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)', borderRadius: '8px', color: '#fff' }} />
                <Area type="monotone" dataKey="active" stroke="var(--info)" strokeWidth={3} fillOpacity={1} fill="url(#colorActive)" name="Active Customers" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
