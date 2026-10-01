import React from 'react';

const AGENTS = [
  { port: 8010, name: 'Compliance', role: 'Gatekeeper', icon: 'verified_user', desc: 'Pre-flight robots.txt & ai.txt gate, rate throttler, regex & NER PII scrubber.', stat1: '0 Violations logged', stat2: 'EDPB 03/2026 Compliant', statusLabel: 'ACTIVE', statusColor: 'var(--tertiary-fixed)', iconColor: 'var(--primary-fixed)', statColor: 'var(--tertiary-fixed)' },
  { port: 8011, name: 'Reader Agent', role: 'Tiered Fetch', icon: 'travel_explore', desc: 'httpx → curl_cffi → Playwright browser pool. Strips script/style DOM.', stat1: '42 DOM pages synced', stat2: 'Latency: 284ms avg', statusLabel: 'CRAWLING', statusColor: 'var(--primary-fixed)', iconColor: 'var(--primary-fixed)', statColor: 'var(--primary-fixed)', pulse: true },
  { port: 8012, name: 'Analyst Agent', role: 'Pydantic Parser', icon: 'psychology', desc: 'Pydantic v2 structured schemas. Normalizes tokens to $/1M & context depth.', stat1: 'Confidence: 0.98', stat2: 'DOM Grounding 100%', statusLabel: 'STABLE', statusColor: 'var(--tertiary-fixed)', iconColor: 'var(--primary-fixed)', statColor: 'var(--tertiary-fixed)' },
  { port: 8013, name: 'Memory / Refl.', role: 'FAISS Vector', icon: 'history_edu', desc: 'Vector diff detector & Reflexion self-healing loop (arXiv:2303.11366).', stat1: '1,420 FAISS Vectors', stat2: '2 Repairs executed', statusLabel: 'BUFFER', statusColor: 'var(--secondary)', iconColor: 'var(--secondary)', statColor: 'var(--secondary)' },
  { port: 8014, name: 'Strategist', role: 'Corroborator', icon: 'radar', desc: 'Enforces ≥2 independent competitor rule. Formulates sales battlecards.', stat1: '2 Macro Trends', stat2: '1 Isolated move', statusLabel: 'SYNTH', statusColor: 'var(--secondary-fixed)', iconColor: 'var(--secondary-fixed)', statColor: 'var(--secondary-fixed)', pulse: true },
  { port: 8015, name: 'Formatter', role: 'Publisher', icon: 'feed', desc: 'Markdown digests, ReportLab styled PDF generation, SSE broadcast.', stat1: 'Brief Generated', stat2: 'Last: 4m ago (PDF ready)', statusLabel: 'IDLE', statusColor: 'var(--tertiary-fixed)', iconColor: 'var(--primary-fixed)', statColor: 'var(--tertiary-fixed)' },
];

function getAgentState(agentStates, agentName) {
  const key = agentName.toLowerCase().replace(/[^a-z]/g, '');
  for (const [k, v] of Object.entries(agentStates)) {
    if (k.includes(key) || key.includes(k)) return v;
  }
  return null;
}

export default function AgentTopology({ agentStates, onSelectAgent, activePipelineStage, onTriggerPipeline, isRunning }) {
  return (
    <section>
      <div className="card-elevated">
        {/* Section Header */}
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--space-md)', paddingBottom: 'var(--space-md)' }}>
          <div className="section-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
              <span className="section-overline">A2A v1.0 Standard Mesh</span>
              <span className="badge badge-cyan" style={{ background: 'rgba(0, 240, 255, 0.08)' }}>Sequential + Async Reflexion</span>
            </div>
            <h2 className="section-title" style={{ fontWeight: 700 }}>Autonomous Agent Swarm Orchestration</h2>
            <p className="section-subtitle">Real-time state machine routing requests from pre-flight legal gating to multi-channel corroboration & publishing.</p>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 'var(--space-xs)' }}>
            <button
              className="btn btn-primary"
              onClick={onTriggerPipeline}
              disabled={isRunning}
              type="button"
              style={isRunning ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
            >
              <span className="material-symbols-outlined">{isRunning ? 'sync' : 'bolt'}</span>
              <span>{isRunning ? 'Swarm Running...' : 'Trigger Autonomous Run'}</span>
            </button>
            <button className="btn btn-secondary" type="button">
              <span className="material-symbols-outlined">travel_explore</span>
              <span>Inspect FAISS Index</span>
            </button>
            <button className="btn btn-ghost" type="button">
              <span className="material-symbols-outlined">pause</span>
              <span>Pause Stream</span>
            </button>
          </div>
        </div>

        {/* Agent Cards Grid */}
        <div className="topology-grid" style={{ paddingTop: 'var(--space-sm)' }}>
          {AGENTS.map((agent, i) => {
            const state = getAgentState(agentStates || {}, agent.name);
            const isActive = activePipelineStage && agent.name.toLowerCase().includes(activePipelineStage);
            let dynamicStatus = agent.statusLabel;
            let dynamicColor = agent.statusColor;
            if (state === 'working') { dynamicStatus = 'WORKING'; dynamicColor = 'var(--primary-fixed)'; }
            if (state === 'completed') { dynamicStatus = 'DONE'; dynamicColor = 'var(--tertiary-fixed)'; }
            if (state === 'failed') { dynamicStatus = 'ERROR'; dynamicColor = 'var(--error)'; }

            return (
              <div
                className="agent-card"
                key={agent.port}
                onClick={() => onSelectAgent && onSelectAgent(agent)}
                style={isActive ? { boxShadow: '0 0 12px rgba(0, 240, 255, 0.15)', borderLeft: '2px solid var(--primary-container)' } : {}}
              >
                <div>
                  <div className="agent-card-header">
                    <span className="badge badge-surface">PORT {agent.port}</span>
                    <span className="text-label-sm" style={{ display: 'flex', alignItems: 'center', gap: 4, color: dynamicColor }}>
                      <span className={`led ${agent.pulse || state === 'working' ? 'animate-ping' : ''}`} style={{ background: dynamicColor }}></span>
                      {dynamicStatus}
                    </span>
                  </div>
                  <div className="agent-icon-row">
                    <div className="agent-icon" style={{ color: agent.iconColor }}>
                      <span className="material-symbols-outlined">{agent.icon}</span>
                    </div>
                    <div>
                      <h3 className="agent-name">{agent.name}</h3>
                      <span className="agent-role">{agent.role}</span>
                    </div>
                  </div>
                  <p className="agent-desc">{agent.desc}</p>
                </div>
                <div className="agent-stats">
                  <div className="stat-primary" style={{ color: agent.statColor }}>{agent.stat1}</div>
                  <div className="stat-secondary">{agent.stat2}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
