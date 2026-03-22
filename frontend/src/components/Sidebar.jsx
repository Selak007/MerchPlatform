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

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div style={{ background: 'var(--primary)', padding: '6px', borderRadius: '8px', display: 'flex' }}>
          <TrendingUp size={24} color="white" />
        </div>
        Lumina Pay
      </div>
      
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button 
              key={item.id}
              className={cn("nav-item", activeTab === item.id && "active", "w-full text-left bg-transparent")}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={20} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <button className="nav-item w-full text-left bg-transparent">
          <Settings size={20} /> Settings
        </button>
        <button className="nav-item w-full text-left bg-transparent" style={{ color: 'var(--danger)' }}>
          <LogOut size={20} /> Logout
        </button>
      </div>
    </aside>
  );
}
