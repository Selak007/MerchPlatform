import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, Send, MessageSquareText } from 'lucide-react';

const SUGGESTED_QUESTIONS = [
  'Show weekend revenue trends',
  'What\'s my fraud risk?',
  'How to improve repeat rate?',
  'Best performing category?',
  'Compare me to industry average',
  'Top customer segments breakdown',
];

export default function Assistant({ merchantId, searchQuery }) {
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      text: 'Hello! I\'m your AI Business Coach. I can help you analyze revenue trends, fraud risks, customer behavior, and pricing strategies. What would you like to explore?',
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateResponse = (userText) => {
    const lower = userText.toLowerCase();
    if (lower.includes('revenue') || lower.includes('weekend')) {
      return 'Based on your transaction data, weekend revenue is approximately 12% lower than weekdays. I recommend introducing a "Weekend Combo" offer — similar merchants have seen a 15% increase in average ticket size with time-limited promotions.';
    }
    if (lower.includes('fraud') || lower.includes('risk')) {
      return 'Your current fraud rate is within acceptable thresholds. However, I\'ve noticed a slight uptick in card-not-present fraud attempts. Consider enabling 3D Secure for transactions above $200 to reduce exposure without impacting checkout conversion.';
    }
    if (lower.includes('repeat') || lower.includes('retention') || lower.includes('loyalty')) {
      return 'Your repeat customer rate could be improved. Currently, a significant portion of your customers are one-time buyers. Consider implementing a points-based loyalty program and personalized email campaigns targeting customers who haven\'t returned in 30+ days.';
    }
    if (lower.includes('category') || lower.includes('product') || lower.includes('performing')) {
      return 'Your top-performing categories show strong revenue concentration. I recommend diversifying promotions across underperforming categories to balance revenue streams and reduce dependency on a single product line.';
    }
    if (lower.includes('industry') || lower.includes('benchmark') || lower.includes('compare')) {
      return 'Compared to industry benchmarks for your MCC code, your average ticket size is competitive. However, your transaction volume has room for growth. Focused marketing during off-peak hours (10am-2pm) could capture untapped demand.';
    }
    if (lower.includes('segment') || lower.includes('customer')) {
      return 'Your customer base breaks down into several key segments. High-value customers represent a smaller portion but drive significant revenue. Consider VIP perks for this group while running acquisition campaigns to grow your mid-tier segment.';
    }
    return 'That\'s a great question! Based on your merchant analytics, I\'d recommend focusing on optimizing your peak hours performance and reducing transaction decline rates. Would you like me to dive deeper into any specific area — revenue, fraud, customers, or pricing?';
  };

  const handleSend = (text) => {
    const msgText = text || input;
    if (!msgText.trim()) return;

    setMessages((prev) => [...prev, { role: 'user', text: msgText }]);
    setInput('');
    setIsTyping(true);

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { role: 'ai', text: generateResponse(msgText) },
      ]);
      setIsTyping(false);
    }, 1500);
  };

  const filteredSuggestions = searchQuery
    ? SUGGESTED_QUESTIONS.filter((q) =>
        q.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : SUGGESTED_QUESTIONS;

  return (
    <div
      className="glass-card"
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        padding: '0',
        overflow: 'hidden',
        border: '1px solid rgba(99, 102, 241, 0.3)',
        minHeight: '500px',
      }}
      data-testid="assistant-page"
    >
      {/* Header */}
      <div
        style={{
          padding: '20px 24px',
          background: 'rgba(99, 102, 241, 0.1)',
          borderBottom: '1px solid var(--card-border)',
          display: 'flex',
          alignItems: 'center',
          gap: '14px',
        }}
      >
        <div
          style={{
            background: 'var(--primary)',
            padding: '10px',
            borderRadius: '12px',
          }}
        >
          <Sparkles size={22} color="#fff" />
        </div>
        <div>
          <h2
            style={{
              fontSize: '20px',
              fontWeight: '600',
              color: '#fff',
              marginBottom: '2px',
            }}
          >
            AI Business Coach
          </h2>
          <p
            style={{
              fontSize: '13px',
              color: 'var(--success)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span
              style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                background: 'var(--success)',
                display: 'inline-block',
              }}
            ></span>
            Online — Analyzing merchant {merchantId === 'all' ? 'platform' : merchantId} data
          </p>
        </div>
      </div>

      {/* Messages Area */}
      <div
        role="log"
        aria-live="polite"
        style={{
          flex: 1,
          padding: '24px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.role}`}>
            {msg.text}
          </div>
        ))}
        {isTyping && (
          <div className="chat-message ai" style={{ opacity: 0.7 }}>
            <span style={{ display: 'inline-flex', gap: '4px' }}>
              <span className="typing-dot">●</span>
              <span className="typing-dot" style={{ animationDelay: '0.2s' }}>●</span>
              <span className="typing-dot" style={{ animationDelay: '0.4s' }}>●</span>
            </span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions (shown when few messages) */}
      {messages.length < 4 && filteredSuggestions.length > 0 && (
        <div
          style={{
            padding: '0 24px 16px',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
          }}
        >
          <p
            style={{
              width: '100%',
              fontSize: '12px',
              fontWeight: '600',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: '4px',
            }}
          >
            Suggested Questions
          </p>
          {filteredSuggestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              style={{
                padding: '8px 16px',
                borderRadius: '20px',
                border: '1px solid var(--card-border)',
                background: 'rgba(99, 102, 241, 0.08)',
                color: 'var(--primary)',
                fontSize: '13px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'var(--transition)',
                whiteSpace: 'nowrap',
              }}
              data-testid={`suggestion-${idx}`}
            >
              <MessageSquareText
                size={12}
                style={{ verticalAlign: 'middle', marginRight: '6px' }}
              />
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div
        style={{
          padding: '20px 24px',
          borderTop: '1px solid var(--card-border)',
          background: 'rgba(0,0,0,0.2)',
        }}
      >
        <div style={{ display: 'flex', gap: '12px' }}>
          <input
            type="text"
            className="chat-input"
            placeholder="Ask about revenue, fraud, customers, pricing..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            aria-label="Chat message input"
          />
          <button
            className="chat-send-btn"
            onClick={() => handleSend()}
            aria-label="Send message"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
