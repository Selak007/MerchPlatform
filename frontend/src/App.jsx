import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import TopHeader from './components/TopHeader';
import Dashboard from './pages/Dashboard';
import Revenue from './pages/Revenue';
import Customers from './pages/Customers';
import Risk from './pages/Risk';
import Insights from './pages/Insights';
import AIAssistantPanel from './components/AIAssistantPanel';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [merchants, setMerchants] = useState([]);
  const [selectedMerchant, setSelectedMerchant] = useState('all');

  useEffect(() => {
    axios.get('http://localhost:5000/api/merchants')
      .then(res => setMerchants(res.data))
      .catch(err => console.error(err));
  }, []);

  const getPageTitle = () => {
    switch(activeTab) {
      case 'dashboard': return 'Business Overview';
      case 'revenue': return 'Revenue & Growth Tracker';
      case 'customers': return 'Customer Insights';
      case 'risk': return 'Fraud Risk Monitor';
      case 'insights': return 'AI Smart Recommendations';
      case 'assistant': return 'AI Business Coach';
      default: return 'Dashboard';
    }
  };

  const renderContent = () => {
    switch(activeTab) {
      case 'dashboard':
        return <Dashboard merchantId={selectedMerchant} />;
      case 'revenue':
        return <Revenue merchantId={selectedMerchant} />;
      case 'customers':
        return <Customers merchantId={selectedMerchant} />;
      case 'risk':
        return <Risk merchantId={selectedMerchant} />;
      case 'insights':
        return <Insights merchantId={selectedMerchant} />;
      default:
        return (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60%', color: 'var(--text-muted)' }}>
            <h2 style={{ fontSize: '24px', marginBottom: '12px', color: '#fff' }}>Section Under Construction</h2>
            <p>The {getPageTitle()} module is currently being developed.</p>
          </div>
        );
    }
  };

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="main-content">
        <TopHeader 
          title={getPageTitle()} 
          merchants={merchants} 
          selectedMerchant={selectedMerchant} 
          setSelectedMerchant={setSelectedMerchant} 
        />
        {renderContent()}
      </main>

      <AIAssistantPanel merchantId={selectedMerchant} />
    </div>
  );
}
