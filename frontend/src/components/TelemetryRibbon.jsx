import React from 'react';

const STATS = [
  { label: 'Target Monitored', icon: 'domain', value: '6 Active', sub: '+60 Models', footer: ['OpenAI, Anthropic, Groq, Mistral', '100% UP'], iconColor: 'var(--primary-fixed)', footerAccent: 'var(--tertiary-fixed)' },
  { label: 'DOM Confidence', icon: 'verified', value: '96.8%', sub: 'Gate ≥ 0.60', footer: ['Grounding verified', 'Zero hallu'], iconColor: 'var(--tertiary-fixed)', valueColor: 'green', footerAccent: 'var(--tertiary-fixed)', progressBar: 96.8 },
  { label: 'Macro Corroboration', icon: 'compare_arrows', value: '4 Verified', sub: '≥2 competitors', footer: ['Input Context War', 'Active Delta'], iconColor: 'var(--secondary)', valueColor: 'purple', footerAccent: 'var(--primary-fixed)' },
  { label: 'Unit Economics', icon: 'monetization_on', value: '$0.13', sub: '/ run avg', footer: ['vs $20k legacy tools', '92% Margin'], iconColor: 'var(--primary-container)', footerAccent: 'var(--tertiary-fixed)' },
  { label: 'Circuit Breakers', icon: 'gavel', value: '0 Trips', sub: 'robots.txt strict', footer: ['PII Scrub rate', '100% Clean'], iconColor: 'var(--tertiary-fixed)', valueColor: 'green', footerAccent: 'var(--tertiary-fixed)' },
];

export default function TelemetryRibbon() {
  return (
    <section>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-sm)', marginBottom: 'var(--space-sm)', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--primary-container)' }} className="animate-ping"></div>
          <span className="text-headline-sm font-semibold" style={{ color: 'var(--primary)' }}>Mission Control: Swarm Topology & A2A Pipeline</span>
          <span className="badge badge-surface">JSON-RPC 2.0 Mesh</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }} className="text-label-sm text-muted">
          <span className="indicator"><span className="material-symbols-outlined" style={{ fontSize: 14, color: 'var(--tertiary-fixed)' }}>format_image_left</span> EDPB 03/2026</span>
          <span>•</span>
          <span className="indicator"><span className="material-symbols-outlined" style={{ fontSize: 14, color: 'var(--primary-fixed)' }}>memory</span> FAISS v1.4</span>
          <span>•</span>
          <span>Auto-Sync: 300ms</span>
        </div>
      </div>
      <div className="stat-grid">
        {STATS.map((s, i) => (
          <div className="stat-card" key={i}>
            <div className="stat-header">
              <span className="stat-label">{s.label}</span>
              <span className="material-symbols-outlined" style={{ fontSize: 16, color: s.iconColor }}>{s.icon}</span>
            </div>
            <div className="stat-value-row">
              <span className={`stat-value ${s.valueColor || ''}`}>{s.value}</span>
              <span className="stat-sub" style={s.valueColor === 'green' ? {} : { color: s.sub.includes('+') ? 'var(--primary-fixed)' : undefined }}>{s.sub}</span>
            </div>
            {s.progressBar && (
              <div className="progress-bar">
                <div className="progress-bar-fill green" style={{ width: `${s.progressBar}%` }}></div>
              </div>
            )}
            <div className="stat-footer" style={s.progressBar ? { marginTop: 'var(--space-xs)' } : {}}>
              <span className="truncate">{s.footer[0]}</span>
              <span className="font-semibold" style={{ color: s.footerAccent }}>{s.footer[1]}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
