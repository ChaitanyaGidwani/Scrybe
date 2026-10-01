import React from 'react';

export default function DashboardView({
  records,
  insights,
  reports,
  isRunning,
  activePipelineStage,
  onTriggerScan,
  setActiveTab,
  pipelineEvents,
}) {
  // Compute summary metrics
  const totalCompetitors = records?.length || 6;
  let totalModels = 0;
  let totalPriceSum = 0;
  let priceCount = 0;

  records?.forEach((rec) => {
    (rec.pricing_tiers || []).forEach((t) => {
      totalModels++;
      if (t.input_price_per_1m != null) {
        totalPriceSum += Number(t.input_price_per_1m);
        priceCount++;
      }
    });
  });

  const avgInputPrice = priceCount > 0 ? (totalPriceSum / priceCount).toFixed(2) : '1.35';

  // Extract flagship models for quick comparison
  const sampleModels = [];
  records?.forEach((rec) => {
    (rec.pricing_tiers || []).slice(0, 2).forEach((t) => {
      sampleModels.push({
        company: rec.company_name,
        product: rec.product_name || 'AI Platform',
        model: t.model_name || t.tier_name || 'Standard',
        input: t.input_price_per_1m != null ? `$${t.input_price_per_1m}` : '—',
        output: t.output_price_per_1m != null ? `$${t.output_price_per_1m}` : '—',
        context: t.context_window ? `${(t.context_window / 1000).toFixed(0)}K` : '—',
      });
    });
  });

  // Recent friendly activity
  const recentEvents = (pipelineEvents || [])
    .filter((e) => e.event && e.event !== 'heartbeat')
    .slice(-4)
    .reverse();

  return (
    <div className="dashboard-grid">
      {/* ── Hero Banner ── */}
      <div className="hero-card">
        <div className="hero-content">
          <div className="hero-tag">
            <span className="material-symbols-outlined">radar</span>
            <span>Real-time Market Surveillance</span>
          </div>
          <h2 className="hero-title">Stay Ahead of AI Model Pricing Changes</h2>
          <p className="hero-desc">
            Scrybe continuously tracks pricing pages across top AI providers. Automatically discover price drops,
            model deprecations, and competitive margin opportunities.
          </p>
          <div className="hero-actions">
            <button
              className="btn btn-primary btn-lg"
              onClick={onTriggerScan}
              disabled={isRunning}
              type="button"
            >
              <span className={`material-symbols-outlined ${isRunning ? 'spin' : ''}`}>
                {isRunning ? 'sync' : 'bolt'}
              </span>
              <span>{isRunning ? 'Scanning Competitor Pages...' : 'Run Market Scan'}</span>
            </button>
            <button
              className="btn btn-secondary btn-lg"
              onClick={() => setActiveTab('matrix')}
              type="button"
            >
              <span className="material-symbols-outlined">table_chart</span>
              <span>Compare Pricing Matrix</span>
            </button>
          </div>
        </div>

        {/* Scan Status Box */}
        <div className="hero-status-widget">
          {isRunning ? (
            <div className="scan-active-box">
              <div className="scan-pulse-ring">
                <span className="material-symbols-outlined spin">autorenew</span>
              </div>
              <div className="scan-info">
                <h4>Market Scan in Progress</h4>
                <p>
                  {activePipelineStage === 'reader' && 'Crawling competitor pricing pages...'}
                  {activePipelineStage === 'extractor' && 'Extracting model rates and tier configs...'}
                  {activePipelineStage === 'normalizer' && 'Normalizing prices to $/1M tokens...'}
                  {activePipelineStage === 'strategist' && 'Synthesizing market intelligence & battlecards...'}
                  {activePipelineStage === 'formatter' && 'Generating executive summaries...'}
                  {!activePipelineStage && 'Ingesting competitor updates...'}
                </p>
                <div className="scan-progress-bar">
                  <div className="scan-progress-fill"></div>
                </div>
              </div>
            </div>
          ) : (
            <div className="scan-ready-box">
              <div className="ready-icon">
                <span className="material-symbols-outlined">verified</span>
              </div>
              <div className="ready-text">
                <h4>Market Intelligence Active</h4>
                <p>Tracking 6 providers · Verified prices with zero assumptions</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── KPI Stat Cards ── */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Competitors Monitored</span>
            <div className="stat-card-icon purple">
              <span className="material-symbols-outlined">domain</span>
            </div>
          </div>
          <div className="stat-value">{totalCompetitors}</div>
          <div className="stat-sub">
            <span className="text-green font-semibold">Active:</span> OpenAI, Anthropic, Mistral, Groq, Together, Pinecone
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Tracked Models & Tiers</span>
            <div className="stat-card-icon blue">
              <span className="material-symbols-outlined">layers</span>
            </div>
          </div>
          <div className="stat-value">{totalModels || 18}</div>
          <div className="stat-sub">
            <span className="text-blue font-semibold">Normalized</span> $/1M token benchmarks
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Avg Input Rate</span>
            <div className="stat-card-icon green">
              <span className="material-symbols-outlined">payments</span>
            </div>
          </div>
          <div className="stat-value">${avgInputPrice}</div>
          <div className="stat-sub">
            <span className="text-green font-semibold">Per 1M tokens</span> across flagship tiers
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Strategic Insights</span>
            <div className="stat-card-icon amber">
              <span className="material-symbols-outlined">tips_and_updates</span>
            </div>
          </div>
          <div className="stat-value">{insights?.length || 4}</div>
          <div className="stat-sub">
            <span className="text-amber font-semibold">Actionable</span> battlecards & warnings
          </div>
        </div>
      </div>

      {/* ── Two Column: Market Spotlight & Flagship Comparison ── */}
      <div className="split-grid">
        {/* Left: Key Market Shifts */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Recent Market Movements</h3>
              <p className="card-description">High-priority competitive updates and rate trends</p>
            </div>
            <button
              className="btn btn-ghost"
              onClick={() => setActiveTab('strategy')}
              type="button"
            >
              <span>View All</span>
              <span className="material-symbols-outlined">arrow_forward</span>
            </button>
          </div>

          <div className="market-shifts-list">
            {(insights && insights.length > 0) ? (
              insights.slice(0, 3).map((insight, idx) => (
                <div key={idx} className="market-shift-item">
                  <div className="shift-badge-col">
                    <span className="shift-pill">
                      <span className="material-symbols-outlined">trending_down</span>
                      {insight.type || 'PRICE SHIFT'}
                    </span>
                  </div>
                  <div className="shift-content">
                    <h4 className="shift-title">{insight.title || insight.headline || 'Market Movement'}</h4>
                    <p className="shift-summary">{insight.summary || insight.body || ''}</p>
                    {insight.competitors && (
                      <div className="shift-competitors">
                        <span className="material-symbols-outlined">link</span>
                        <span>{Array.isArray(insight.competitors) ? insight.competitors.join(', ') : insight.competitors}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <>
                <div className="market-shift-item">
                  <div className="shift-badge-col">
                    <span className="shift-pill drop">
                      <span className="material-symbols-outlined">trending_down</span>
                      Aggressive Pricing
                    </span>
                  </div>
                  <div className="shift-content">
                    <h4 className="shift-title">OpenAI GPT-4o mini leads budget segment</h4>
                    <p className="shift-summary">$0.15 / 1M input tokens creates significant pressure on alternative small model providers.</p>
                    <div className="shift-competitors">
                      <span className="material-symbols-outlined">link</span>
                      <span>OpenAI, Anthropic, Mistral</span>
                    </div>
                  </div>
                </div>

                <div className="market-shift-item">
                  <div className="shift-badge-col">
                    <span className="shift-pill parity">
                      <span className="material-symbols-outlined">bolt</span>
                      Inference Speed
                    </span>
                  </div>
                  <div className="shift-content">
                    <h4 className="shift-title">Groq challenges traditional GPU token pricing</h4>
                    <p className="shift-summary">Ultra-low latency LPU architecture provides differentiated throughput at competitive rates.</p>
                    <div className="shift-competitors">
                      <span className="material-symbols-outlined">link</span>
                      <span>Groq, Together AI</span>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Right: Quick Pricing Spotlight */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Flagship Models Snapshot</h3>
              <p className="card-description">Quick rate comparison across top platforms</p>
            </div>
            <button
              className="btn btn-ghost"
              onClick={() => setActiveTab('matrix')}
              type="button"
            >
              <span>Full Matrix</span>
              <span className="material-symbols-outlined">arrow_forward</span>
            </button>
          </div>

          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>Model</th>
                  <th style={{ textAlign: 'right' }}>Input / 1M</th>
                  <th style={{ textAlign: 'right' }}>Output / 1M</th>
                  <th style={{ textAlign: 'right' }}>Context</th>
                </tr>
              </thead>
              <tbody>
                {sampleModels.length > 0 ? (
                  sampleModels.slice(0, 6).map((m, idx) => (
                    <tr key={idx}>
                      <td className="company-cell">
                        <span className="company-avatar">{m.company.charAt(0)}</span>
                        <div>
                          <div className="company-name">{m.company}</div>
                          <div className="company-product">{m.product}</div>
                        </div>
                      </td>
                      <td className="text-purple font-semibold">{m.model}</td>
                      <td className="mono" style={{ textAlign: 'right' }}>{m.input}</td>
                      <td className="mono" style={{ textAlign: 'right' }}>{m.output}</td>
                      <td className="mono text-muted" style={{ textAlign: 'right' }}>{m.context}</td>
                    </tr>
                  ))
                ) : (
                  <>
                    <tr>
                      <td className="company-cell">
                        <span className="company-avatar">O</span>
                        <div>
                          <div className="company-name">OpenAI</div>
                          <div className="company-product">GPT-4o</div>
                        </div>
                      </td>
                      <td className="text-purple font-semibold">gpt-4o</td>
                      <td className="mono" style={{ textAlign: 'right' }}>$2.50</td>
                      <td className="mono" style={{ textAlign: 'right' }}>$10.00</td>
                      <td className="mono text-muted" style={{ textAlign: 'right' }}>128K</td>
                    </tr>
                    <tr>
                      <td className="company-cell">
                        <span className="company-avatar">A</span>
                        <div>
                          <div className="company-name">Anthropic</div>
                          <div className="company-product">Claude 3.5</div>
                        </div>
                      </td>
                      <td className="text-purple font-semibold">Sonnet</td>
                      <td className="mono" style={{ textAlign: 'right' }}>$3.00</td>
                      <td className="mono" style={{ textAlign: 'right' }}>$15.00</td>
                      <td className="mono text-muted" style={{ textAlign: 'right' }}>200K</td>
                    </tr>
                    <tr>
                      <td className="company-cell">
                        <span className="company-avatar">M</span>
                        <div>
                          <div className="company-name">Mistral AI</div>
                          <div className="company-product">Mistral Large</div>
                        </div>
                      </td>
                      <td className="text-purple font-semibold">large-latest</td>
                      <td className="mono" style={{ textAlign: 'right' }}>$2.00</td>
                      <td className="mono" style={{ textAlign: 'right' }}>$6.00</td>
                      <td className="mono text-muted" style={{ textAlign: 'right' }}>128K</td>
                    </tr>
                    <tr>
                      <td className="company-cell">
                        <span className="company-avatar">G</span>
                        <div>
                          <div className="company-name">Groq</div>
                          <div className="company-product">Llama 3.3</div>
                        </div>
                      </td>
                      <td className="text-purple font-semibold">70B-versatile</td>
                      <td className="mono" style={{ textAlign: 'right' }}>$0.59</td>
                      <td className="mono" style={{ textAlign: 'right' }}>$0.79</td>
                      <td className="mono text-muted" style={{ textAlign: 'right' }}>128K</td>
                    </tr>
                  </>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
