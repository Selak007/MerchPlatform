import React, { useState, useMemo } from 'react';
import { Calendar, ChevronDown } from 'lucide-react';

/**
 * DateRangePicker — glassmorphism-styled date range selector
 * with quick-select buttons (Today, 7d, 30d, 90d, YTD).
 *
 * Props:
 *   dateRange: { from: string|null, to: string|null }
 *   onDateRangeChange: (range: { from: string|null, to: string|null }) => void
 */
export default function DateRangePicker({ dateRange, onDateRangeChange }) {
  const [isOpen, setIsOpen] = useState(false);

  const toISODate = (d) => d.toISOString().split('T')[0];

  const quickSelects = useMemo(() => {
    const now = new Date();
    const today = toISODate(now);

    const daysAgo = (n) => {
      const d = new Date(now);
      d.setDate(d.getDate() - n);
      return toISODate(d);
    };

    const ytdStart = toISODate(new Date(now.getFullYear(), 0, 1));

    return [
      { label: 'Today', from: today, to: today },
      { label: '7d', from: daysAgo(7), to: today },
      { label: '30d', from: daysAgo(30), to: today },
      { label: '90d', from: daysAgo(90), to: today },
      { label: 'YTD', from: ytdStart, to: today },
      { label: 'All Time', from: null, to: null },
    ];
  }, []);

  const activeLabel = useMemo(() => {
    if (!dateRange || (!dateRange.from && !dateRange.to)) return 'All Time';
    const match = quickSelects.find(
      (q) => q.from === dateRange.from && q.to === dateRange.to
    );
    if (match) return match.label;
    return `${dateRange.from || '...'} — ${dateRange.to || '...'}`;
  }, [dateRange, quickSelects]);

  const handleQuickSelect = (qs) => {
    onDateRangeChange({ from: qs.from, to: qs.to });
    setIsOpen(false);
  };

  const handleCustomChange = (field, value) => {
    onDateRangeChange({
      ...dateRange,
      [field]: value || null,
    });
  };

  const containerStyle = {
    position: 'relative',
    display: 'inline-block',
  };

  const triggerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    background: 'var(--card-bg)',
    border: '1px solid var(--card-border)',
    borderRadius: '12px',
    padding: '8px 14px',
    color: '#fff',
    fontSize: '13px',
    cursor: 'pointer',
    backdropFilter: 'blur(10px)',
    transition: 'var(--transition)',
    whiteSpace: 'nowrap',
  };

  const dropdownStyle = {
    position: 'absolute',
    top: 'calc(100% + 8px)',
    right: '0',
    background: 'rgba(26, 28, 43, 0.95)',
    backdropFilter: 'blur(20px)',
    border: '1px solid var(--card-border)',
    borderRadius: '16px',
    padding: '16px',
    zIndex: 50,
    minWidth: '280px',
    boxShadow: '0 16px 48px rgba(0,0,0,0.4)',
  };

  const quickBtnStyle = (isActive) => ({
    padding: '6px 14px',
    borderRadius: '8px',
    border: isActive ? '1px solid var(--primary)' : '1px solid var(--card-border)',
    background: isActive ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.05)',
    color: isActive ? 'var(--primary)' : 'var(--text-muted)',
    fontSize: '12px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'var(--transition)',
  });

  const inputStyle = {
    background: 'rgba(0,0,0,0.3)',
    border: '1px solid var(--card-border)',
    borderRadius: '8px',
    padding: '8px 12px',
    color: '#fff',
    fontSize: '13px',
    outline: 'none',
    width: '100%',
    fontFamily: 'inherit',
  };

  return (
    <div style={containerStyle} data-testid="date-range-picker">
      {/* Trigger Button */}
      <button
        style={triggerStyle}
        onClick={() => setIsOpen(!isOpen)}
        data-testid="date-range-trigger"
      >
        <Calendar size={14} color="var(--primary)" />
        <span>{activeLabel}</span>
        <ChevronDown size={14} color="var(--text-muted)" style={{
          transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'var(--transition)',
        }} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div style={dropdownStyle} data-testid="date-range-dropdown">
          {/* Quick Select Buttons */}
          <p style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '10px' }}>
            Quick Select
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
            {quickSelects.map((qs) => (
              <button
                key={qs.label}
                style={quickBtnStyle(activeLabel === qs.label)}
                onClick={() => handleQuickSelect(qs)}
                data-testid={`quick-select-${qs.label.toLowerCase().replace(/\s/g, '-')}`}
              >
                {qs.label}
              </button>
            ))}
          </div>

          {/* Custom Date Inputs */}
          <p style={{ fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '10px' }}>
            Custom Range
          </p>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="date"
              style={inputStyle}
              value={dateRange?.from || ''}
              onChange={(e) => handleCustomChange('from', e.target.value)}
              data-testid="date-from-input"
            />
            <span style={{ color: 'var(--text-muted)', fontSize: '12px', flexShrink: 0 }}>to</span>
            <input
              type="date"
              style={inputStyle}
              value={dateRange?.to || ''}
              onChange={(e) => handleCustomChange('to', e.target.value)}
              data-testid="date-to-input"
            />
          </div>
        </div>
      )}
    </div>
  );
}
