import React from 'react';

export default function StrategicView({ insights, records }) {
  return (
    <section>
      <div className="card-elevated">
        <div style={{ paddingBottom: 'var(--space-md)' }}>
          <div className="section-header">
            <span className="section-overline">Strategic Intelligence Engine</span>
            <h2 className="section-title" style={{ fontWeight: 700 }}>Executive Intelligence & Battlecards</h2>
            <p className="section-subtitle">Corroborated macro trends, competitive delta shifts, and actionable sales battlecard intelligence.</p>
          </div>
        </div>

        {insights && insights.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: 'var(--space-md)' }}>
            {insights.map((insight, i) => (
              <div className="alert-card" key={i}>
                <div className="alert-gradient-bar cyan-purple"></div>
                <div className="alert-header" style={{ paddingTop: 4 }}>
                  <span className="badge badge-green font-bold" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span className="led led-green" style={{ width: 6, height: 6 }}></span>
                    {insight.type || 'STRATEGIC INSIGHT'}
                  </span>
                  {insight.confidence && (
                    <span className="text-label-sm text-green">Conf: {typeof insight.confidence === 'number' ? `${(insight.confidence * 100).toFixed(0)}%` : insight.confidence}</span>
                  )}
                </div>
                <h4 className="alert-title">{insight.title || insight.headline || 'Untitled Insight'}</h4>
                <p className="alert-body">{insight.summary || insight.body || insight.description || ''}</p>
                {insight.competitors && (
                  <div className="alert-footer">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 14, color: 'var(--tertiary-fixed)' }}>link</span>
                      <span>{Array.isArray(insight.competitors) ? insight.competitors.join(', ') : insight.competitors}</span>
                    </div>
                    {insight.battlecard_id && <span className="text-cyan">Battlecard #{insight.battlecard_id}</span>}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--outline)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 48, display: 'block', marginBottom: 'var(--space-sm)' }}>insights</span>
            <p className="text-body-lg">No strategic insights generated yet.</p>
            <p className="text-body-sm text-muted">Run the autonomous pipeline to produce corroborated intelligence.</p>
          </div>
        )}

        {/* Compact Pricing Summary */}
        {records && records.length > 0 && (
          <div style={{ marginTop: 'var(--space-lg)', paddingTop: 'var(--space-md)', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
            <h3 className="text-headline-sm font-semibold" style={{ marginBottom: 'var(--space-sm)' }}>Quick Matrix Reference</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-sm)' }}>
              {records.slice(0, 6).map((rec, i) => (
                <div key={i} style={{ padding: 'var(--space-sm)', borderRadius: 'var(--radius-lg)', background: 'var(--surface-container)', minWidth: 180, flex: '1 1 180px' }}>
                  <div className="text-label-sm text-muted" style={{ marginBottom: 2 }}>{rec.company_name}</div>
                  <div className="text-headline-sm font-semibold text-cyan">{rec.product_name || '—'}</div>
                  <div className="text-label-sm text-dim" style={{ marginTop: 4 }}>
                    {rec.pricing_tiers && rec.pricing_tiers.length > 0 ? `${rec.pricing_tiers.length} models extracted` : 'No tiers'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
