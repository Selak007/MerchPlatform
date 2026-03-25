import React, { useState, useEffect, useRef } from 'react';
import { Search, User } from 'lucide-react';
import NotificationDropdown from './NotificationDropdown';

export default function TopHeader({ title, merchants, selectedMerchant, setSelectedMerchant, onSearch }) {
  const [searchQuery, setSearchQuery] = useState('');
  const debounceRef = useRef(null);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (onSearch) onSearch(searchQuery);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery, onSearch]);

  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter' && onSearch) {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      onSearch(searchQuery);
    }
  };

  return (
    <header className="top-header">
      <h1 className="page-title">{title}</h1>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* Merchant Dropdown */}
        <select 
          value={selectedMerchant}
          onChange={(e) => setSelectedMerchant(e.target.value)}
          aria-label="Select merchant"
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
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            aria-label="Search insights"
            style={{ 
              background: 'transparent', border: 'none', color: '#fff', 
              outline: 'none', width: '200px', fontSize: '14px' 
            }} 
          />
        </div>
        
        <NotificationDropdown merchantId={selectedMerchant} />

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
