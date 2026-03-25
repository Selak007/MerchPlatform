import React from 'react';
import { LayoutDashboard, TrendingUp, Users, ShieldAlert, BarChart3, Settings, LogOut, MessageSquareText } from 'lucide-react';
import { cn } from '../lib/utils';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'revenue', label: 'Revenue & Growth', icon: TrendingUp },
    { id: 'customers', label: 'Customers', icon: Users },
    { id: 'risk', label: 'Risk & Fraud', icon: ShieldAlert },
    { id: 'insights', label: 'AI Insights', icon: BarChart3 },
    { id: 'assistant', label: 'AI Assistant', icon: MessageSquareText },
  ];

  const handleLogout = () => {
    window.confirm('Are you sure you want to logout?');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div style={{ background: 'var(--primary)', padding: '6px', borderRadius: '8px', display: 'flex' }}>
          <TrendingUp size={24} color="white" />
        </div>
        <span>Lumina Pay</span>
      </div>
      
      <nav className="sidebar-nav" role="navigation" aria-label="Main navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button 
              key={item.id}
              className={cn("nav-item", activeTab === item.id && "active", "w-full text-left bg-transparent")}
              onClick={() => setActiveTab(item.id)}
              aria-label={item.label}
              aria-current={activeTab === item.id ? 'page' : undefined}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <button
          className={cn("nav-item", activeTab === 'settings' && "active", "w-full text-left bg-transparent")}
          onClick={() => setActiveTab('settings')}
          aria-label="Settings"
        >
          <Settings size={20} /> <span>Settings</span>
        </button>
        <button
          className="nav-item w-full text-left bg-transparent"
          style={{ color: 'var(--danger)' }}
          onClick={handleLogout}
          aria-label="Logout"
        >
          <LogOut size={20} /> <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
