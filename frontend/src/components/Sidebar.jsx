import React from 'react';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
  { id: 'matrix', label: 'Price Comparison', icon: 'table_chart' },
  { id: 'strategy', label: 'Market Insights', icon: 'insights' },
  { id: 'reports', label: 'Executive Reports', icon: 'article' },
  { id: 'competitors', label: 'Tracked Competitors', icon: 'domain' },
];

export default function Sidebar({ activeTab, setActiveTab, wsConnected, isRunning }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo-icon">
          <span className="material-symbols-outlined">visibility</span>
        </div>
        <div className="sidebar-logo-text">
          <span className="name">Scrybe</span>
          <span className="tagline">Market Intelligence</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">MENU</div>
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            type="button"
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            <span className="material-symbols-outlined">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status-card">
          <div className="status-indicator-row">
            <span className={`status-dot ${isRunning ? 'pulse' : wsConnected ? 'online' : 'offline'}`}></span>
            <span className="status-label">
              {isRunning ? 'Scan in progress...' : wsConnected ? 'Live Market Feed' : 'Connecting...'}
            </span>
          </div>
          <span className="status-sub">
            {isRunning ? 'Updating competitor data' : '6 competitors monitored'}
          </span>
        </div>
      </div>
    </aside>
  );
}
