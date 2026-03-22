import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Sparkles, TrendingUp, Tag, BarChart3 } from 'lucide-react';

const API_URL = 'http://localhost:5000/api';

export default function Insights({ merchantId }) {
  const [recommendations, setRecommendations] = useState([]);
  const [pricingSignal, setPricingSignal] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const id = merchantId && merchantId !== 'all' ? merchantId : 1;
        const res = await axios.get(`${API_URL}/merchant/${id}/dashboard`);
        setRecommendations(res.data.recommendations || []);
        setPricingSignal(res.data.pricing_signal || null);
      } catch (err) {
        console.error('Error fetching insights:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [merchantId]);

  if (loading) {
    return <div className="glass-card skeleton" style={{ height: '400px' }}></div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div className="glass-card">
        <div className="card-header">
          <h3 className="card-title"><Sparkles size={24} color="var(--primary)" /> AI Revenue Booster & Pricing Advisor</h3>
        </div>
        <p style={{ color: 'var(--text-muted)', marginBottom: '24px', fontSize: '15px' }}>
          Powered by real transaction analytics — merchant-specific and dynamic.
        </p>
        <div className="grid-cols-2">
          {recommendations.map((rec, idx) => (
            <div key={idx} style={{
              background: 'rgba(255,255,255,0.03)', border: '1px solid var(--card-border)',
              borderRadius: '16px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px'
            }}>
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                <div style={{
                  width: '48px', height: '48px', borderRadius: '12px', flexShrink: 0,
                  background: rec.type === 'Revenue Booster' ? 'rgba(16,185,129,0.15)' : rec.type === 'Pricing Advisor' ? 'rgba(245,158,11,0.15)' : 'rgba(59,130,246,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: rec.type === 'Revenue Booster' ? 'var(--success)' : rec.type === 'Pricing Advisor' ? 'var(--warning)' : 'var(--info)'
                }}>
                  {rec.type === 'Pricing Advisor' ? <Tag size={24} /> : rec.type === 'Revenue Booster' ? <TrendingUp size={24} /> : <BarChart3 size={24} />}
                </div>
                <div>
                  <span style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--primary)' }}>{rec.type}</span>
                  <h4 style={{ fontSize: '16px', color: '#fff', marginTop: '4px' }}>{rec.text}</h4>
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '16px' }}>
                <div>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Expected Revenue Impact</p>
                  <p style={{ fontSize: '20px', fontWeight: '700', color: 'var(--success)' }}>+${rec.impact || '—'}</p>
                </div>
                <div>
                  <span style={{ padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '700',
                    background: rec.priority === 'High' ? 'rgba(16,185,129,0.15)' : 'rgba(99,102,241,0.15)',
                    color: rec.priority === 'High' ? 'var(--success)' : 'var(--primary)' }}>
                    {rec.priority} Priority
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
