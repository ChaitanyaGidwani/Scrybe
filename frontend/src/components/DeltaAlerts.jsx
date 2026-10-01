import React from 'react';

const SAMPLE_ALERTS = [
  {
    type: 'MACRO SHIFT • CORROBORATED',
    badgeClass: 'badge-green',
    gradient: 'cyan-purple',
    confidence: '99.1%',
    confColor: 'var(--tertiary-fixed)',
    title: 'Input Context Cache Rate War (-33%)',
    body: 'Anthropic Claude 3.5 Sonnet & Mistral Large simultaneously reduce prompt cache write tariffs to accelerate long-context enterprise ingestion.',
    footer: { left: 'Anthropic DOM + Mistral Platform API', leftIcon: 'link', right: 'Strategic Battlecard #42', rightColor: 'var(--primary-fixed)' },
  },
  {
    type: 'ISOLATED MOVE • SINGLE SOURCE',
    badgeClass: 'badge-purple',
    gradient: 'purple-cyan',
    confidence: '94.4%',
    confColor: 'var(--secondary-fixed)',
    title: 'Groq Deploys Llama 3.3 70B Batch Tariff',
    body: 'Groq announces sub-$0.60 batch inference ($0.59/1M in, $0.79/1M out) on LPUs. Strategist Agent flagged awaiting rival price match before macro rating.',
    footer: { left: 'Source: Groq API Release Doc', leftIcon: 'pending', right: 'Awaiting second competitor', rightColor: 'var(--outline)' },
  },
  {
    type: 'REFLEXION SELF-REPAIR (arXiv:2303.11366)',
    badgeClass: 'badge-cyan',
    gradient: 'green-cyan',
    confidence: 'Pass: Iter 2',
    confColor: 'var(--tertiary-fixed)',
    title: 'Together AI Pricing DOM Selector Healed',
    body: 'Analyst Agent triggered self-critique loop after React hydration shifted classes. Memory buffer provided structural semantic anchor.',
    footer: { left: 'Zero Human Intervention Required', leftIcon: 'auto_fix_high', right: 'hash: e38f72', rightColor: 'var(--outline)' },
  },
];

export default function DeltaAlerts({ insights }) {
  const alerts = insights && insights.length > 0 ? insights : SAMPLE_ALERTS;

  return (
    <div className="card-elevated" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 'var(--space-sm)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
          <span className="material-symbols-outlined" style={{ fontSize: 20, color: 'var(--primary-container)' }}>lightbulb</span>
          <span className="text-headline-sm font-semibold">Verified Delta Alerts</span>
        </div>
        <span className="badge badge-green font-medium">{alerts.length} New Shifts</span>
      </div>

      {/* Alert Stack */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
        {alerts.map((alert, i) => (
          <div className="alert-card" key={i}>
            <div className={`alert-gradient-bar ${alert.gradient || 'cyan-purple'}`}></div>
            <div className="alert-header" style={{ paddingTop: 4 }}>
              <span className={`badge ${alert.badgeClass || 'badge-green'} font-bold`} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span className="led" style={{ background: alert.confColor, width: 6, height: 6 }}></span>
                {alert.type}
              </span>
              <span className="text-label-sm" style={{ color: alert.confColor }}>
                {alert.confidence ? (alert.confidence.includes('%') ? `Conf: ${alert.confidence}` : alert.confidence) : ''}
              </span>
            </div>
            <h4 className="alert-title">{alert.title}</h4>
            <p className="alert-body">{alert.body}</p>
            <div className="alert-footer">
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                {alert.footer.leftIcon && (
                  <span className="material-symbols-outlined" style={{ fontSize: 14, color: alert.footer.rightColor === 'var(--outline)' ? 'var(--secondary)' : 'var(--tertiary-fixed)' }}>{alert.footer.leftIcon}</span>
                )}
                <span>{alert.footer.left}</span>
              </div>
              <span style={{ color: alert.footer.rightColor }}>{alert.footer.right}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Benchmark Footer */}
      <div style={{ marginTop: 'var(--space-md)', padding: 'var(--space-sm)', borderRadius: 'var(--radius)', background: 'var(--surface-lowest)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
          <span className="material-symbols-outlined" style={{ fontSize: 18, color: 'var(--tertiary-fixed)' }}>fact_check</span>
          <span className="text-body-sm">Golden Benchmark Catalog</span>
        </div>
        <a href="#" className="text-label-sm text-cyan" style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <span>Review Grounding Data</span>
          <span className="material-symbols-outlined" style={{ fontSize: 14 }}>arrow_forward</span>
        </a>
      </div>
    </div>
  );
}
