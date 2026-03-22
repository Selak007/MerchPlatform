import React, { useState } from 'react';
import { MessageSquareText, Send, Sparkles, X } from 'lucide-react';

export default function AIAssistantPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Hello! I am your AI Business Coach. I noticed a 12% revenue drop on weekends. Want to discuss strategies?' }
  ]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;
    
    setMessages(prev => [...prev, { role: 'user', text: input }]);
    setInput('');
    
    // Simulate AI response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        role: 'ai', 
        text: 'Based on your transaction data, I recommend introducing a "Weekend Combo" offer. Similar merchants have seen a 15% increase in average ticket size.' 
      }]);
    }, 1500);
  };

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        style={{
          position: 'fixed', bottom: '32px', right: '32px',
          width: '64px', height: '64px', borderRadius: '50%',
          background: 'var(--primary)', border: 'none',
          boxShadow: '0 8px 32px var(--primary-glow)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', zIndex: 100, transition: 'var(--transition)'
        }}
        className="hover:scale-110"
      >
        <Sparkles size={28} color="#fff" />
      </button>
    );
  }

  return (
    <div className="glass-card" style={{
      position: 'fixed', bottom: '32px', right: '32px', width: '380px', height: '560px',
      display: 'flex', flexDirection: 'column', padding: '0', overflow: 'hidden',
      zIndex: 100, boxShadow: '0 24px 64px rgba(0,0,0,0.4)', border: '1px solid rgba(99, 102, 241, 0.3)'
    }}>
      {/* Header */}
      <div style={{
        padding: '20px', background: 'rgba(99, 102, 241, 0.1)', borderBottom: '1px solid var(--card-border)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'var(--primary)', padding: '8px', borderRadius: '10px' }}>
            <Sparkles size={18} color="#fff" />
          </div>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#fff', marginBottom: '2px' }}>AI Business Coach</h3>
            <p style={{ fontSize: '12px', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--success)' }}></span> Online
            </p>
          </div>
        </div>
        <button onClick={() => setIsOpen(false)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
          <X size={20} />
        </button>
      </div>

      {/* Messages Area */}
      <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.role}`}>
            {msg.text}
          </div>
        ))}
      </div>

      {/* Input Area */}
      <div style={{ padding: '20px', borderTop: '1px solid var(--card-border)', background: 'rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', gap: '12px' }}>
          <input 
            type="text" 
            className="chat-input" 
            placeholder="Ask about revenue, fraud, etc..." 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          />
          <button className="chat-send-btn" onClick={handleSend}>
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
