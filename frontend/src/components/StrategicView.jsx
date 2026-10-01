import React, { useState } from 'react';

const FALLBACK_INSIGHTS = [
  {
    type: 'Price War Alert',
    badgeClass: 'badge-amber',
    icon: 'warning',
    title: 'Aggressive Sub-Dollar Commodity Token Race',
    summary:
      'OpenAI and Mistral have slashed prices on small footprint models (GPT-4o mini and Mistral NeMo). Input tokens dropped under $0.15/1M, making lightweight conversational tiers virtually free for basic utility tasks.',
    recommendation:
      'Evaluate migrating high-volume non-reasoning workflows (classification, summarization, routing) to mini/small models to capture immediate 60-80% cost reduction.',
    competitors: ['OpenAI', 'Mistral AI', 'Anthropic'],
    impact: 'High',
  },
  {
    type: 'Margin Opportunity',
    badgeClass: 'badge-green',
    icon: 'trending_up',
    title: 'Prompt Caching Generates 75% Cost Asymmetry',
    summary:
      'Providers supporting persistent prompt caching (Anthropic Claude 3.5 Sonnet and OpenAI GPT-4o) offer write/read cache pricing at up to 75% discount over regular input tokens.',
    recommendation:
      'Standardize system prompts and large context prefixes into warm cache blocks to radically lower per-request inference expenditure.',
    competitors: ['Anthropic', 'OpenAI'],
    impact: 'High',
  },
  {
    type: 'Inference Throughput',
    badgeClass: 'badge-purple',
    icon: 'bolt',
    title: 'LPU Acceleration Challenges Standard Cloud APIs',
    summary:
      'Groq delivers 500+ tokens/second inference on open models at prices lower than traditional GPU cloud hosts, making real-time voice and iterative agent loops viable.',
    recommendation:
      'Benchmark latency-sensitive features on dedicated LPU endpoints for interactive user experiences where TTFT (time-to-first-token) is critical.',
    competitors: ['Groq', 'Together AI'],
    impact: 'Medium',
  },
  {
    type: 'Context Economics',
    badgeClass: 'badge-blue',
    icon: 'psychology',
    title: 'Long-Context (200K+) Pricing Stability',
    summary:
      'Frontier model long-context input costs have stabilized around $2.50 to $3.00/1M tokens, avoiding premium multi-tier surcharges previously seen in earlier architectures.',
    recommendation:
      'Consolidate multi-document RAG pipelines into direct whole-document context windows where needle-in-haystack accuracy is required.',
    competitors: ['Anthropic', 'OpenAI'],
    impact: 'Medium',
  },
];

export default function StrategicView({ insights, records }) {
  const [filterType, setFilterType] = useState('ALL');

  // Merge backend insights with fallback defaults if backend returned empty
  const activeInsights =
    insights && insights.length > 0
      ? insights.map((ins, i) => ({
          type: ins.type || 'Market Observation',
          badgeClass:
            (ins.type || '').toLowerCase().includes('price') || (ins.type || '').toLowerCase().includes('war')
              ? 'badge-amber'
              : (ins.type || '').toLowerCase().includes('margin') || (ins.type || '').toLowerCase().includes('opportunity')
              ? 'badge-green'
              : 'badge-purple',
          icon: 'lightbulb',
          title: ins.title || ins.headline || `Market Insight #${i + 1}`,
          summary: ins.summary || ins.body || ins.description || 'Analysis of current market movements.',
          recommendation:
            ins.recommendation ||
            'Review internal model routing to take advantage of these competitive shifts.',
          competitors: Array.isArray(ins.competitors)
            ? ins.competitors
            : ins.competitors
            ? [ins.competitors]
            : ['Industry Wide'],
          impact: ins.confidence ? (ins.confidence > 0.8 ? 'High' : 'Medium') : 'Medium',
        }))
      : FALLBACK_INSIGHTS;

  const filtered = activeInsights.filter((ins) => {
    if (filterType === 'ALL') return true;
    if (filterType === 'PRICING') {
      return ins.type.toLowerCase().includes('price') || ins.type.toLowerCase().includes('margin');
    }
    if (filterType === 'TECH') {
      return !ins.type.toLowerCase().includes('price') && !ins.type.toLowerCase().includes('margin');
    }
    return true;
  });

  return (
    <div className="strategy-page">
      {/* ── Top Bar with Filter Chips ── */}
      <div className="card-header" style={{ marginBottom: 20 }}>
        <div>
          <h2 className="card-title" style={{ fontSize: 20 }}>Strategic Intelligence & Takeaways</h2>
          <p className="card-description">
            Synthesized insights, market trends, and recommended actions for product and commercial leaders.
          </p>
        </div>

        <div className="filter-chips">
          <button
            type="button"
            className={`filter-chip ${filterType === 'ALL' ? 'active' : ''}`}
            onClick={() => setFilterType('ALL')}
          >
            All Insights ({activeInsights.length})
          </button>
          <button
            type="button"
            className={`filter-chip ${filterType === 'PRICING' ? 'active' : ''}`}
            onClick={() => setFilterType('PRICING')}
          >
            Pricing & Margins
          </button>
          <button
            type="button"
            className={`filter-chip ${filterType === 'TECH' ? 'active' : ''}`}
            onClick={() => setFilterType('TECH')}
          >
            Performance & Strategy
          </button>
        </div>
      </div>

      {/* ── Insight Cards Grid ── */}
      <div className="insights-grid">
        {filtered.map((item, idx) => (
          <div key={idx} className="insight-card">
            <div className="insight-header">
              <div className="insight-tag-row">
                <span className={`badge ${item.badgeClass}`}>
                  <span className="material-symbols-outlined" style={{ fontSize: 13 }}>
                    {item.icon}
                  </span>
                  {item.type}
                </span>
                <span className="text-muted" style={{ fontSize: 12 }}>
                  Impact: <strong>{item.impact}</strong>
                </span>
              </div>
            </div>

            <h3 className="insight-title">{item.title}</h3>
            <p className="insight-body">{item.summary}</p>

            <div className="insight-recommendation-box">
              <div className="rec-label">
                <span className="material-symbols-outlined">lightbulb</span>
                <span>RECOMMENDED ACTION</span>
              </div>
              <p className="rec-text">{item.recommendation}</p>
            </div>

            <div className="insight-footer">
              <div className="insight-competitor-tags">
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>link</span>
                <span>Impacted:</span>
                {item.competitors.map((c, ci) => (
                  <span key={ci} className="competitor-pill-mini">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
