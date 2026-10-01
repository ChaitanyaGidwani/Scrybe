import React from 'react';

export default function AgentCardModal({ agent, onClose }) {
  if (!agent) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 24, color: 'var(--primary-container)' }}>
              {agent.icon || 'smart_toy'}
            </span>
            <h3 className="text-headline-md font-bold">{agent.name || 'Agent'}</h3>
          </div>
          <button className="btn-icon" onClick={onClose}>
            <span className="material-symbols-outlined" style={{ fontSize: 20 }}>close</span>
          </button>
        </div>

        {/* Agent Details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          {/* Role Badge + Port */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', flexWrap: 'wrap' }}>
            <span className="badge badge-surface">PORT {agent.port || '—'}</span>
            <span className="badge badge-purple">{agent.role || 'Agent'}</span>
            {agent.statusLabel && (
              <span className="badge badge-green" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span className="led led-green" style={{ width: 6, height: 6 }}></span>
                {agent.statusLabel}
              </span>
            )}
          </div>

          {/* Description */}
          <p className="text-body-md text-muted">
            {agent.desc || agent.description || 'No description available.'}
          </p>

          {/* Stats Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-sm)' }}>
            <div style={{ padding: 'var(--space-sm)', borderRadius: 'var(--radius-lg)', background: 'var(--surface-lowest)' }}>
              <div className="text-label-sm text-muted" style={{ marginBottom: 4 }}>PRIMARY METRIC</div>
              <div className="text-headline-sm font-semibold text-cyan">{agent.stat1 || '—'}</div>
            </div>
            <div style={{ padding: 'var(--space-sm)', borderRadius: 'var(--radius-lg)', background: 'var(--surface-lowest)' }}>
              <div className="text-label-sm text-muted" style={{ marginBottom: 4 }}>SECONDARY METRIC</div>
              <div className="text-headline-sm font-semibold text-green">{agent.stat2 || '—'}</div>
            </div>
          </div>

          {/* Agent Card / A2A Schema */}
          <div style={{ padding: 'var(--space-md)', borderRadius: 'var(--radius-lg)', background: 'var(--surface-lowest)' }}>
            <div className="text-label-sm text-muted" style={{ marginBottom: 'var(--space-sm)' }}>A2A AGENT CARD (JSON-RPC 2.0)</div>
            <pre className="text-code" style={{ color: 'var(--on-surface)', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
{JSON.stringify({
  name: agent.name,
  port: agent.port,
  role: agent.role,
  protocol: 'JSON-RPC 2.0',
  capabilities: ['tasks/send', 'tasks/get', 'tasks/cancel'],
  status: agent.statusLabel || 'unknown',
}, null, 2)}
            </pre>
          </div>
        </div>

        {/* Footer */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-sm)', paddingTop: 'var(--space-xs)' }}>
          <button className="btn btn-ghost" onClick={onClose}>Close</button>
          <button className="btn btn-primary">
            <span className="material-symbols-outlined">terminal</span>
            Inspect RPC
          </button>
        </div>
      </div>
    </div>
  );
}
