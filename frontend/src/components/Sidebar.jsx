import React from 'react';

const NAV_ITEMS = [
  { id: 'topology', icon: 'hub', label: 'Autonomous Pipeline' },
  { id: 'matrix', icon: 'table_chart', label: 'Pricing & Feature Matrix' },
  { id: 'strategy', icon: 'insights', label: 'Executive Intelligence' },
  { id: 'compliance', icon: 'verified_user', label: 'Compliance & Audit' },
  { id: 'reports', icon: 'smart_toy', label: 'A2A Agent Swarm' },
];

export default function Sidebar({ activeTab, setActiveTab, wsConnected }) {
  return (
    <aside className="sidebar">
      <div>
        {/* Brand Header */}
        <div className="sidebar-header">
          <svg width="32" height="32" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="48" stroke="#00f0ff" strokeWidth="2" fill="#0a0e17"/>
            <path d="M50 18L72 42H60V58H72L50 82L28 58H40V42H28L50 18Z" fill="#00f0ff" fillOpacity="0.9"/>
            <path d="M50 28L64 42H56V58H64L50 72L36 58H44V42H36L50 28Z" fill="#0a0e17"/>
            <circle cx="50" cy="50" r="6" fill="#00f0ff"/>
          </svg>
          <div className="sidebar-brand">
            <span className="sidebar-brand-name">SCRYBE</span>
            <span className="sidebar-brand-sub">SWARM SYNTHESIS</span>
          </div>
        </div>

        {/* Context Profile */}
        <div className="sidebar-context">
          <div className="sidebar-context-card">
            <span className="sidebar-context-label">Active Context Profile</span>
            <div className="sidebar-context-value">
              <span>B2B AI & LLM Matrix</span>
              <span className="material-symbols-outlined" style={{ fontSize: 16, color: 'var(--on-surface-variant)' }}>unfold_more</span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          {NAV_ITEMS.map(item => (
            <a
              key={item.id}
              className={`nav-item${activeTab === item.id ? ' active' : ''}`}
              onClick={() => setActiveTab(item.id)}
              href="#"
              role="button"
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span>{item.label}</span>
            </a>
          ))}
        </nav>
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="sidebar-status-card">
          <div className="sidebar-status-row">
            <span className="text-label-sm text-muted">CONSENSUS LOAD</span>
            <span className="text-label-sm text-green">6/6 ACTIVE</span>
          </div>
          <div className="sidebar-status-bar">
            <div className="sidebar-status-bar-fill" style={{ width: '100%' }}></div>
          </div>
        </div>
        <div className="sidebar-mesh-info">
          <span className="text-label-sm" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
            <span className={`led ${wsConnected ? 'pulse' : ''}`} style={{ background: wsConnected ? 'var(--tertiary-fixed)' : 'var(--error)' }}></span>
            {wsConnected ? 'RPC MESH' : 'OFFLINE'}
          </span>
          <span className="text-label-sm text-dim">v0.2.0</span>
        </div>
      </div>
    </aside>
  );
}
