import React from 'react';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: 'space_dashboard' },
  { id: 'matrix', label: 'Pricing Comparison', icon: 'table_chart' },
  { id: 'strategy', label: 'Insights', icon: 'lightbulb' },
  { id: 'reports', label: 'Reports', icon: 'description' },
];

export default function Sidebar({ activeTab, setActiveTab, wsConnected }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo-icon">
          <span className="material-symbols-outlined">eagle</span>
        </div>
        <div className="sidebar-logo-text">
          <span className="name">Scrybe</span>
          <span className="tagline">Market Intelligence</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(item => (
          <div
            key={item.id}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            <span className="material-symbols-outlined">{item.icon}</span>
            <span>{item.label}</span>
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className={`status-dot ${wsConnected ? 'online' : 'offline'}`}></span>
          <span className="status-label">
            <strong>{wsConnected ? 'Connected' : 'Offline'}</strong> — {wsConnected ? 'Live data stream' : 'Reconnecting...'}
          </span>
        </div>
      </div>
    </aside>
  );
}
