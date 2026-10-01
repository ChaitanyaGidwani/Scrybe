import React from 'react';

const TAB_TITLES = {
  dashboard: { title: 'Market Overview', subtitle: 'Real-time AI model pricing & competitor movements' },
  matrix: { title: 'Pricing Comparison', subtitle: 'Side-by-side normalized pricing across all competitors' },
  strategy: { title: 'Market Insights', subtitle: 'Actionable executive takeaways, price shifts, and opportunities' },
  verdict: { title: 'Final Strategic Verdict', subtitle: 'Optimal model routing, margin maximization, and cost optimization' },
  reports: { title: 'Executive Reports', subtitle: 'Published market briefs and intelligence digests' },
  competitors: { title: 'Tracked Competitors', subtitle: '6 active AI providers monitored across the web' },
};

export default function TopHeader({
  activeTab,
  wsConnected,
  isRunning,
  onTriggerScan,
  lastUpdated,
  searchQuery,
  setSearchQuery,
  onExport,
}) {
  const current = TAB_TITLES[activeTab] || TAB_TITLES.dashboard;

  return (
    <header className="top-bar">
      <div className="top-bar-left">
        <div>
          <h1 className="page-title">{current.title}</h1>
          <p className="page-subtitle">{current.subtitle}</p>
        </div>
      </div>

      <div className="top-bar-center">
        <div className="search-bar">
          <span className="material-symbols-outlined search-icon">search</span>
          <input
            type="text"
            placeholder="Search models, companies, or pricing..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button className="clear-search-btn" onClick={() => setSearchQuery('')}>
              <span className="material-symbols-outlined">close</span>
            </button>
          )}
        </div>
      </div>

      <div className="top-bar-right">
        {lastUpdated && (
          <span className="last-updated-badge">
            <span className="material-symbols-outlined">schedule</span>
            <span>{lastUpdated}</span>
          </span>
        )}

        <button
          className="btn btn-secondary"
          onClick={onExport}
          title="Export CSV of current pricing data"
          type="button"
        >
          <span className="material-symbols-outlined">download</span>
          <span>Export CSV</span>
        </button>

        <button
          className={`btn ${isRunning ? 'btn-scanning' : 'btn-primary'}`}
          onClick={onTriggerScan}
          disabled={isRunning}
          type="button"
        >
          <span className={`material-symbols-outlined ${isRunning ? 'spin' : ''}`}>
            {isRunning ? 'sync' : 'bolt'}
          </span>
          <span>{isRunning ? 'Scanning Market...' : 'Scan Competitors'}</span>
        </button>
      </div>
    </header>
  );
}
