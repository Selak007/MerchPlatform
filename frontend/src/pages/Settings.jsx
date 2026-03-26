import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Palette, AlertTriangle, Globe, User, Save, RotateCcw } from 'lucide-react';
import { useTheme } from '../context/ThemeContext.jsx';

const STORAGE_KEY = 'lumina-pay-settings';

const DEFAULT_SETTINGS = {
  theme: 'dark',
  currency: 'USD',
  fraudRateThreshold: 3,
  declineRateThreshold: 15,
  lowRepeatRateThreshold: 30,
  apiBaseUrl: 'http://localhost:5000',
  merchantName: 'Merchant Admin',
  merchantEmail: 'admin@luminapay.com',
};

function loadSettings() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
    }
  } catch (_e) {
    // ignore
  }
  return { ...DEFAULT_SETTINGS };
}

function saveSettings(settings) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch (_e) {
    // ignore
  }
}

export default function Settings() {
  const [settings, setSettings] = useState(loadSettings);
  const [saved, setSaved] = useState(false);
  const { setTheme } = useTheme();

  const update = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
    // If the theme is being changed, update the context immediately
    if (key === 'theme') {
      setTheme(value);
    }
  };

  const handleSave = () => {
    saveSettings(settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const handleReset = () => {
    setSettings({ ...DEFAULT_SETTINGS });
    saveSettings(DEFAULT_SETTINGS);
    setTheme(DEFAULT_SETTINGS.theme);
    setSaved(false);
  };

  // ── Shared Styles ──────────────────────────────────────
  const cardStyle = {
    background: 'var(--card-bg)',
    backdropFilter: 'blur(16px)',
    border: '1px solid var(--card-border)',
    borderRadius: '16px',
    padding: '24px',
    boxShadow: 'var(--shadow-card)',
  };

  const labelStyle = {
    fontSize: '13px',
    fontWeight: '600',
    color: 'var(--text-muted)',
    marginBottom: '8px',
    display: 'block',
  };

  const inputStyle = {
    width: '100%',
    padding: '10px 14px',
    borderRadius: '10px',
    border: '1px solid var(--card-border)',
    background: 'var(--bg-inset-light)',
    color: 'var(--text-heading)',
    fontSize: '14px',
    fontFamily: 'inherit',
    outline: 'none',
    transition: 'var(--transition)',
  };

  const selectStyle = {
    ...inputStyle,
    cursor: 'pointer',
    appearance: 'auto',
  };

  const btnPrimary = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 24px',
    borderRadius: '12px',
    border: 'none',
    background: 'var(--primary)',
    color: '#fff',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'var(--transition)',
    boxShadow: '0 4px 12px var(--primary-glow)',
  };

  const btnSecondary = {
    ...btnPrimary,
    background: 'var(--bg-overlay)',
    boxShadow: 'none',
    border: '1px solid var(--card-border)',
    color: 'var(--text-heading)',
  };

  const sectionTitle = (icon, title) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
      {icon}
      <h3 style={{ fontSize: '18px', fontWeight: '600', color: 'var(--text-heading)' }}>{title}</h3>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }} data-testid="settings-page">
      {/* Save Bar */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '16px 24px', borderRadius: '16px',
        background: saved ? 'rgba(16,185,129,0.1)' : 'var(--card-bg)',
        border: saved ? '1px solid rgba(16,185,129,0.3)' : '1px solid var(--card-border)',
        transition: 'var(--transition)',
      }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: 'var(--text-heading)', marginBottom: '4px' }}>
            <SettingsIcon size={20} style={{ verticalAlign: 'middle', marginRight: '8px' }} />
            Platform Settings
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            {saved ? '✓ Settings saved successfully' : 'Configure your dashboard preferences and alert thresholds'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button style={btnSecondary} onClick={handleReset} data-testid="reset-btn">
            <RotateCcw size={16} /> Reset
          </button>
          <button style={btnPrimary} onClick={handleSave} data-testid="save-btn">
            <Save size={16} /> Save Changes
          </button>
        </div>
      </div>

      {/* Grid Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '24px' }}>

        {/* Display Preferences */}
        <div style={cardStyle} data-testid="display-preferences">
          {sectionTitle(<Palette size={20} color="var(--primary)" />, 'Display Preferences')}

          <div style={{ marginBottom: '20px' }}>
            <label style={labelStyle}>Theme</label>
            <div style={{ display: 'flex', gap: '12px' }}>
              {['dark', 'light'].map((t) => (
                <button
                  key={t}
                  onClick={() => update('theme', t)}
                  data-testid={`theme-${t}`}
                  style={{
                    flex: 1,
                    padding: '12px',
                    borderRadius: '10px',
                    border: settings.theme === t ? '2px solid var(--primary)' : '1px solid var(--card-border)',
                    background: settings.theme === t ? 'rgba(99,102,241,0.15)' : 'var(--bg-subtle)',
                    color: settings.theme === t ? 'var(--primary)' : 'var(--text-muted)',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    textTransform: 'capitalize',
                    transition: 'var(--transition)',
                  }}
                >
                  {t === 'dark' ? '🌙' : '☀️'} {t}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label style={labelStyle} htmlFor="currency-select">Currency Format</label>
            <select
              id="currency-select"
              style={selectStyle}
              value={settings.currency}
              onChange={(e) => update('currency', e.target.value)}
              data-testid="currency-select"
            >
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
              <option value="GBP">GBP (£)</option>
              <option value="INR">INR (₹)</option>
            </select>
          </div>
        </div>

        {/* Alert Thresholds */}
        <div style={cardStyle} data-testid="alert-thresholds">
          {sectionTitle(<AlertTriangle size={20} color="var(--warning)" />, 'Alert Thresholds')}

          {[
            { key: 'fraudRateThreshold', label: 'Fraud Rate Threshold (%)', min: 0.5, max: 20, step: 0.5 },
            { key: 'declineRateThreshold', label: 'Decline Rate Threshold (%)', min: 1, max: 50, step: 1 },
            { key: 'lowRepeatRateThreshold', label: 'Low Repeat Rate Threshold (%)', min: 5, max: 80, step: 5 },
          ].map((field) => (
            <div key={field.key} style={{ marginBottom: '20px' }}>
              <label style={labelStyle} htmlFor={field.key}>{field.label}</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <input
                  type="range"
                  id={field.key}
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  value={settings[field.key]}
                  onChange={(e) => update(field.key, parseFloat(e.target.value))}
                  style={{ flex: 1, accentColor: 'var(--primary)' }}
                  data-testid={`slider-${field.key}`}
                />
                <span style={{
                  minWidth: '48px', textAlign: 'center',
                  padding: '4px 8px', borderRadius: '6px',
                  background: 'rgba(99,102,241,0.15)', color: 'var(--primary)',
                  fontSize: '14px', fontWeight: '700',
                }}>
                  {settings[field.key]}%
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* API Configuration (spans 2 columns) */}
        <div style={{ ...cardStyle, gridColumn: 'span 2' }} data-testid="api-configuration">
          {sectionTitle(<Globe size={20} color="var(--info)" />, 'API Configuration')}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <label style={labelStyle} htmlFor="api-base-url">Backend API URL</label>
              <input
                id="api-base-url"
                type="url"
                style={inputStyle}
                value={settings.apiBaseUrl}
                onChange={(e) => update('apiBaseUrl', e.target.value)}
                placeholder="http://localhost:5000"
                data-testid="api-url-input"
              />
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px' }}>
                The base URL for all API requests. Changes take effect on next page load.
              </p>
            </div>
            <div>
              <label style={labelStyle}>Connection Status</label>
              <div style={{
                padding: '12px 16px', borderRadius: '10px',
                background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)',
                display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)', boxShadow: '0 0 8px var(--success)' }}></div>
                <span style={{ fontSize: '14px', color: 'var(--success)', fontWeight: '600' }}>Connected</span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginLeft: 'auto' }}>{settings.apiBaseUrl}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Profile (spans 2 columns) */}
        <div style={{ ...cardStyle, gridColumn: 'span 2' }} data-testid="profile-section">
          {sectionTitle(<User size={20} color="var(--secondary)" />, 'Profile')}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <label style={labelStyle} htmlFor="merchant-name">Merchant Name</label>
              <input
                id="merchant-name"
                type="text"
                style={{ ...inputStyle, opacity: 0.7 }}
                value={settings.merchantName}
                readOnly
                data-testid="merchant-name-input"
              />
            </div>
            <div>
              <label style={labelStyle} htmlFor="merchant-email">Email</label>
              <input
                id="merchant-email"
                type="email"
                style={{ ...inputStyle, opacity: 0.7 }}
                value={settings.merchantEmail}
                readOnly
                data-testid="merchant-email-input"
              />
            </div>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '12px' }}>
            Profile information is read-only in this version. Contact support to update.
          </p>
        </div>
      </div>
    </div>
  );
}
