import React from 'react';
import { Bell, Search, User } from 'lucide-react';

export default function TopHeader({ title, merchants, selectedMerchant, setSelectedMerchant }) {
  return (
    <header className="top-header">
      <h1 className="page-title">{title}</h1>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* Merchant Dropdown */}
        <select 
          value={selectedMerchant}
          onChange={(e) => setSelectedMerchant(e.target.value)}
          style={{
            background: 'var(--card-bg)', border: '1px solid var(--primary)', borderRadius: '12px',
            color: '#fff', padding: '8px 16px', fontSize: '14px', outline: 'none', cursor: 'pointer',
            backdropFilter: 'blur(10px)'
          }}
        >
          <option value="all">All Merchants (Platform View)</option>
          {merchants && merchants.map(m => (
            <option key={m.merchant_id} value={m.merchant_id}>
              {m.merchant_name}
            </option>
          ))}
        </select>

        <div style={{ 
          display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.3)', 
          borderRadius: '20px', padding: '8px 16px', border: '1px solid var(--card-border)' 
        }}>
          <Search size={16} color="var(--text-muted)" style={{ marginRight: '8px' }} />
          <input 
            type="text" 
            placeholder="Search insights..." 
            style={{ 
              background: 'transparent', border: 'none', color: '#fff', 
              outline: 'none', width: '200px', fontSize: '14px' 
            }} 
          />
        </div>
        
        <button style={{ 
          background: 'rgba(255,255,255,0.05)', border: '1px solid var(--card-border)',
          width: '40px', height: '40px', borderRadius: '50%', display: 'flex', 
          alignItems: 'center', justifyContent: 'center', cursor: 'pointer', position: 'relative'
        }}>
          <Bell size={18} color="#fff" />
          <span style={{ 
            position: 'absolute', top: '8px', right: '10px', width: '8px', 
            height: '8px', background: 'var(--danger)', borderRadius: '50%',
            boxShadow: '0 0 10px var(--danger)'
          }}></span>
        </button>

        <div style={{ 
          display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer',
          padding: '6px 12px', borderRadius: '20px', background: 'rgba(255,255,255,0.05)',
          border: '1px solid var(--card-border)'
        }}>
          <div style={{ 
            width: '32px', height: '32px', borderRadius: '50%', 
            background: 'var(--primary)', display: 'flex', alignItems: 'center', 
            justifyContent: 'center' 
          }}>
            <User size={16} color="#fff" />
          </div>
          <span style={{ fontSize: '14px', fontWeight: '500', color: '#fff' }}>Merchant</span>
        </div>
      </div>
    </header>
  );
}
