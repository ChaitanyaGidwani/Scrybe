import React, { useState } from 'react';

const DEFAULT_COMPETITORS = [
  {
    name: 'OpenAI',
    category: 'LLM & Multimodal Tokens',
    pricingUrl: 'https://openai.com/pricing',
    status: 'Active',
    modelsCount: '6 models tracked',
    flagship: 'GPT-4o, GPT-4o mini, o1-preview',
    description: 'Industry benchmark for frontier reasoning, general-purpose LLM, and embeddings.',
    color: '#10a37f',
    initial: 'O',
  },
  {
    name: 'Anthropic',
    category: 'Reasoning & Frontier Tokens',
    pricingUrl: 'https://www.anthropic.com/pricing',
    status: 'Active',
    modelsCount: '4 models tracked',
    flagship: 'Claude 3.5 Sonnet, Claude 3.5 Haiku, Opus',
    description: 'Leading code generation and long-context (200K) reasoning models.',
    color: '#d97706',
    initial: 'A',
  },
  {
    name: 'Mistral AI',
    category: 'European Open-Weight & Commercial APIs',
    pricingUrl: 'https://mistral.ai/technology/#pricing',
    status: 'Active',
    modelsCount: '5 models tracked',
    flagship: 'Mistral Large 2, Codestral, Pixtral',
    description: 'High efficiency multilingual and open-weight models hosted via European endpoints.',
    color: '#f97316',
    initial: 'M',
  },
  {
    name: 'Groq',
    category: 'Ultra Low-Latency Inference',
    pricingUrl: 'https://groq.com/pricing/',
    status: 'Active',
    modelsCount: '3 models tracked',
    flagship: 'Llama 3.3 70B, Llama 3.1 8B',
    description: 'LPU inference engine delivering 500+ tokens/sec throughput at budget rates.',
    color: '#f43f5e',
    initial: 'G',
  },
  {
    name: 'Together AI',
    category: 'Open Source Cloud Inference',
    pricingUrl: 'https://www.together.ai/pricing',
    status: 'Active',
    modelsCount: '8 models tracked',
    flagship: 'Llama-3, Qwen-2.5, DeepSeek',
    description: 'Broadest selection of open-source fine-tunes and dedicated cluster instances.',
    color: '#6366f1',
    initial: 'T',
  },
  {
    name: 'Pinecone',
    category: 'Vector Database & Retrieval',
    pricingUrl: 'https://www.pinecone.io/pricing/',
    status: 'Active',
    modelsCount: '3 tiers tracked',
    flagship: 'Serverless, Standard, Enterprise',
    description: 'Dedicated vector index pricing based on read/write units and storage GB.',
    color: '#0ea5e9',
    initial: 'P',
  },
];

export default function CompetitorsView({ records }) {
  const [filter, setFilter] = useState('');

  const competitors = DEFAULT_COMPETITORS.map((comp) => {
    // Match with actual records if available
    const matchedRecord = records?.find(
      (r) => r.company_name?.toLowerCase().includes(comp.name.toLowerCase())
    );
    return {
      ...comp,
      actualTiers: matchedRecord?.pricing_tiers?.length,
      lastUrl: matchedRecord?.source_url || comp.pricingUrl,
      confidence: matchedRecord?.extraction_confidence,
    };
  });

  const filtered = competitors.filter(
    (c) =>
      c.name.toLowerCase().includes(filter.toLowerCase()) ||
      c.category.toLowerCase().includes(filter.toLowerCase()) ||
      c.flagship.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="competitors-page">
      <div className="card-header" style={{ marginBottom: 24 }}>
        <div>
          <h2 className="card-title" style={{ fontSize: 20 }}>Monitored Competitors</h2>
          <p className="card-description">
            6 AI providers actively scanned for real-time pricing updates and model changes.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <div className="search-bar" style={{ width: 260 }}>
            <span className="material-symbols-outlined search-icon">search</span>
            <input
              type="text"
              placeholder="Filter providers..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="competitors-grid">
        {filtered.map((comp, idx) => (
          <div key={idx} className="competitor-card">
            <div className="competitor-card-header">
              <div
                className="competitor-avatar"
                style={{ backgroundColor: `${comp.color}20`, color: comp.color }}
              >
                {comp.initial}
              </div>
              <div className="competitor-name-wrap">
                <h3 className="competitor-name">{comp.name}</h3>
                <span className="competitor-category">{comp.category}</span>
              </div>
              <span className="badge badge-green">
                <span className="material-symbols-outlined" style={{ fontSize: 12 }}>check_circle</span>
                {comp.status}
              </span>
            </div>

            <p className="competitor-desc">{comp.description}</p>

            <div className="competitor-meta-row">
              <div className="competitor-meta-item">
                <span className="meta-label">Models Tracked</span>
                <span className="meta-val">
                  {comp.actualTiers ? `${comp.actualTiers} tiers live` : comp.modelsCount}
                </span>
              </div>
              <div className="competitor-meta-item">
                <span className="meta-label">Primary Models</span>
                <span className="meta-val truncate" title={comp.flagship}>{comp.flagship}</span>
              </div>
            </div>

            <div className="competitor-card-footer">
              <a
                href={comp.lastUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="competitor-link"
              >
                <span className="material-symbols-outlined">open_in_new</span>
                <span>View Pricing Page</span>
              </a>
              <span className="text-muted" style={{ fontSize: 12 }}>
                Auto-scanned
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
