import React from 'react';

export default function MatrixView({ records, pipelineId, onRefresh }) {
  return (
    <section>
      <div className="card-elevated">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 'var(--space-md)', flexWrap: 'wrap', gap: 'var(--space-sm)' }}>
          <div className="section-header">
            <span className="section-overline">Pricing Intelligence Matrix</span>
            <h2 className="section-title" style={{ fontWeight: 700 }}>Competitive Pricing & Feature Grid</h2>
            <p className="section-subtitle">Extracted, normalized ($/1M tokens), and DOM-grounded from live competitor pricing pages.</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
            {pipelineId && <span className="badge badge-cyan">Pipeline: {pipelineId}</span>}
            <button className="btn btn-secondary" onClick={onRefresh}>
              <span className="material-symbols-outlined">refresh</span>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {records && records.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>COMPANY</th>
                  <th>PRODUCT</th>
                  <th>TIER / MODEL</th>
                  <th style={{ textAlign: 'right' }}>INPUT $/1M</th>
                  <th style={{ textAlign: 'right' }}>OUTPUT $/1M</th>
                  <th style={{ textAlign: 'right' }}>CACHE $/1M</th>
                  <th style={{ textAlign: 'right' }}>CONTEXT</th>
                  <th>CONFIDENCE</th>
                  <th>SOURCE</th>
                </tr>
              </thead>
              <tbody>
                {records.map((rec, i) => {
                  const tiers = rec.pricing_tiers || [];
                  if (tiers.length === 0) {
                    return (
                      <tr key={i}>
                        <td style={{ fontWeight: 600 }}>{rec.company_name}</td>
                        <td>{rec.product_name || '—'}</td>
                        <td colSpan={7} className="text-muted">No tiers extracted</td>
                      </tr>
                    );
                  }
                  return tiers.map((tier, j) => (
                    <tr key={`${i}-${j}`}>
                      {j === 0 && <td rowSpan={tiers.length} style={{ fontWeight: 600, verticalAlign: 'top', borderRight: '1px solid rgba(255,255,255,0.04)' }}>{rec.company_name}</td>}
                      {j === 0 && <td rowSpan={tiers.length} className="text-muted" style={{ verticalAlign: 'top' }}>{rec.product_name || '—'}</td>}
                      <td className="text-cyan">{tier.model_name || tier.tier_name || '—'}</td>
                      <td className="numeric">{tier.input_price_per_1m != null ? `$${tier.input_price_per_1m}` : '—'}</td>
                      <td className="numeric">{tier.output_price_per_1m != null ? `$${tier.output_price_per_1m}` : '—'}</td>
                      <td className="numeric text-muted">{tier.cache_price_per_1m != null ? `$${tier.cache_price_per_1m}` : '—'}</td>
                      <td className="numeric text-muted">{tier.context_window ? `${(tier.context_window / 1000).toFixed(0)}K` : '—'}</td>
                      {j === 0 && (
                        <td rowSpan={tiers.length} style={{ verticalAlign: 'top' }}>
                          <span className={`badge ${(rec.extraction_confidence || 0) >= 0.9 ? 'badge-green' : (rec.extraction_confidence || 0) >= 0.6 ? 'badge-cyan' : 'badge-amber'}`}>
                            {((rec.extraction_confidence || 0) * 100).toFixed(0)}%
                          </span>
                        </td>
                      )}
                      {j === 0 && (
                        <td rowSpan={tiers.length} className="text-muted truncate" style={{ verticalAlign: 'top', maxWidth: 180 }}>
                          {rec.source_url ? new URL(rec.source_url).hostname : '—'}
                        </td>
                      )}
                    </tr>
                  ));
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--outline)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 48, display: 'block', marginBottom: 'var(--space-sm)' }}>table_chart</span>
            <p className="text-body-lg">No pricing data extracted yet.</p>
            <p className="text-body-sm text-muted">Trigger a pipeline run to crawl and extract competitor pricing.</p>
          </div>
        )}
      </div>
    </section>
  );
}
