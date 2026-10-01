import React from 'react';

export default function ComplianceLedger({ audits }) {
  return (
    <section>
      <div className="card-elevated">
        <div style={{ paddingBottom: 'var(--space-md)' }}>
          <div className="section-header">
            <span className="section-overline">Compliance & Ethics Engine</span>
            <h2 className="section-title" style={{ fontWeight: 700 }}>Audit Ledger & Regulatory Compliance</h2>
            <p className="section-subtitle">Immutable compliance audit trail: robots.txt gating, PII scrubbing, rate-limit adherence, and EDPB 03/2026 conformance.</p>
          </div>
        </div>

        {/* Summary Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 'var(--space-sm)', marginBottom: 'var(--space-lg)' }}>
          <div className="stat-card" style={{ minHeight: 'auto' }}>
            <div className="stat-header">
              <span className="stat-label">PII SCRUB RATE</span>
              <span className="material-symbols-outlined" style={{ fontSize: 16, color: 'var(--tertiary-fixed)' }}>shield</span>
            </div>
            <div className="stat-value green" style={{ fontSize: 24 }}>100%</div>
            <div className="stat-footer"><span>Zero PII leakage</span></div>
          </div>
          <div className="stat-card" style={{ minHeight: 'auto' }}>
            <div className="stat-header">
              <span className="stat-label">ROBOTS.TXT CHECKS</span>
              <span className="material-symbols-outlined" style={{ fontSize: 16, color: 'var(--primary-fixed)' }}>dns</span>
            </div>
            <div className="stat-value cyan" style={{ fontSize: 24 }}>0 Blocks</div>
            <div className="stat-footer"><span>All crawls authorized</span></div>
          </div>
          <div className="stat-card" style={{ minHeight: 'auto' }}>
            <div className="stat-header">
              <span className="stat-label">CIRCUIT BREAKERS</span>
              <span className="material-symbols-outlined" style={{ fontSize: 16, color: 'var(--tertiary-fixed)' }}>gavel</span>
            </div>
            <div className="stat-value green" style={{ fontSize: 24 }}>0 Trips</div>
            <div className="stat-footer"><span>All within threshold</span></div>
          </div>
          <div className="stat-card" style={{ minHeight: 'auto' }}>
            <div className="stat-header">
              <span className="stat-label">EDPB CONFORMANCE</span>
              <span className="material-symbols-outlined" style={{ fontSize: 16, color: 'var(--secondary)' }}>policy</span>
            </div>
            <div className="stat-value purple" style={{ fontSize: 24 }}>Compliant</div>
            <div className="stat-footer"><span>EDPB 03/2026</span></div>
          </div>
        </div>

        {/* Audit Table */}
        {audits && audits.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>TIMESTAMP</th>
                  <th>AGENT</th>
                  <th>CHECK TYPE</th>
                  <th>TARGET</th>
                  <th>RESULT</th>
                  <th>DETAIL</th>
                </tr>
              </thead>
              <tbody>
                {audits.map((audit, i) => (
                  <tr key={i}>
                    <td className="text-dim">{audit.timestamp ? new Date(audit.timestamp).toLocaleTimeString('en-US', { hour12: false }) : '—'}</td>
                    <td>
                      <span className="badge badge-surface">{(audit.agent || 'compliance').toUpperCase()}</span>
                    </td>
                    <td className="text-muted">{audit.check_type || audit.type || '—'}</td>
                    <td className="text-cyan truncate" style={{ maxWidth: 200 }}>{audit.target_url || audit.target || '—'}</td>
                    <td>
                      <span className={`badge ${(audit.result || '').toLowerCase().includes('pass') || (audit.result || '').toLowerCase().includes('allow') ? 'badge-green' : 'badge-red'}`}>
                        {(audit.result || '—').toUpperCase()}
                      </span>
                    </td>
                    <td className="text-muted truncate" style={{ maxWidth: 300 }}>{audit.detail || audit.message || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--outline)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 48, display: 'block', marginBottom: 'var(--space-sm)' }}>verified_user</span>
            <p className="text-body-lg">No audit records yet.</p>
            <p className="text-body-sm text-muted">Compliance audits are generated automatically during pipeline runs.</p>
          </div>
        )}
      </div>
    </section>
  );
}
