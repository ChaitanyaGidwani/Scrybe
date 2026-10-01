import React from 'react';

export default function TopHeader({ wsConnected, isRunning, onTriggerPipeline, pipelineMode, setPipelineMode }) {
  return (
    <header className="top-header">
      <div className="header-left">
        {/* Version Badge */}
        <div className="header-version-badge">
          <span className="text-cyan font-semibold">v0.2.0</span>
          <span className="text-dim">|</span>
          <span className="text-green">{wsConnected ? 'A2A-RPC ACTIVE' : 'DISCONNECTED'}</span>
        </div>

        {/* Profile Bar */}
        <div className="header-profile-bar">
          <span className="material-symbols-outlined">travel_explore</span>
          <span className="header-profile-text">Profile: OpenAI, Anthropic, Groq, Mistral, Together, Pinecone</span>
        </div>

        {/* Live Indicators */}
        <div className="header-indicators">
          <span className="indicator">
            <span className={`indicator-dot ${wsConnected ? 'green' : 'amber'}`}></span>
            {wsConnected ? '6/6 HEALTHY' : 'CHECKING...'}
          </span>
          <span className="indicator">
            <span className={`indicator-dot ${wsConnected ? 'cyan' : 'amber'}`}></span>
            {wsConnected ? 'STREAM CONNECTED' : 'STREAM PENDING'}
          </span>
        </div>
      </div>

      <div className="header-right">
        {/* Mode Selector */}
        <select
          className="btn btn-secondary"
          value={pipelineMode}
          onChange={e => setPipelineMode(e.target.value)}
          style={{ cursor: 'pointer', appearance: 'auto', paddingRight: 'var(--space-md)' }}
        >
          <option value="in_process">In-Process</option>
          <option value="remote">Remote A2A</option>
        </select>

        <button className="btn btn-secondary" type="button">
          <span className="material-symbols-outlined">terminal</span>
          <span>API Docs</span>
        </button>

        <button className="btn btn-secondary" type="button">
          <span className="material-symbols-outlined">picture_as_pdf</span>
          <span>Export PDF</span>
        </button>

        <button
          className="btn btn-primary"
          onClick={onTriggerPipeline}
          disabled={isRunning}
          type="button"
          style={isRunning ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
        >
          <span className="material-symbols-outlined">{isRunning ? 'sync' : 'play_arrow'}</span>
          <span>{isRunning ? 'Running...' : 'Trigger Run'}</span>
        </button>

        <div className="header-divider"></div>

        <button className="btn-icon" type="button">
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>settings</span>
        </button>

        <div className="user-avatar">
          <span className="material-symbols-outlined">person</span>
        </div>
      </div>
    </header>
  );
}
