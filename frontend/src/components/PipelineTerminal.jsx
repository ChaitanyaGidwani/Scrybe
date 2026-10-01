import React, { useRef, useEffect, useState } from 'react';

function getAgentTagClass(agent) {
  const a = (agent || '').toLowerCase();
  if (a.includes('compliance') || a.includes('orchestrator') || a.includes('pipeline')) return 'cyan';
  if (a.includes('reader') || a.includes('analyst') || a.includes('formatter')) return 'cyan';
  if (a.includes('memory') || a.includes('reflexion') || a.includes('strategist')) return 'purple';
  return 'cyan';
}

function getEventBadge(event) {
  const ev = (event || '').toLowerCase();
  if (ev.includes('completed') || ev.includes('done') || ev.includes('pass')) return 'badge-green';
  if (ev.includes('failed') || ev.includes('error')) return 'badge-red';
  if (ev.includes('start') || ev.includes('working') || ev.includes('progress')) return 'badge-cyan';
  if (ev.includes('flag') || ev.includes('warning') || ev.includes('isolated')) return 'badge-amber';
  return 'badge-surface';
}

function formatTimestamp(ts) {
  if (!ts) return '—';
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return ts;
  }
}

export default function PipelineTerminal({ events, isRunning, pipelineId, onClear }) {
  const containerRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [activeTermTab, setActiveTermTab] = useState('stream');

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events, autoScroll]);

  const filteredEvents = events.slice(-200);

  return (
    <div className="terminal-container">
      {/* Terminal Header */}
      <div className="terminal-header">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="terminal-dots">
            <span className="terminal-dot red"></span>
            <span className="terminal-dot purple"></span>
            <span className="terminal-dot green"></span>
          </div>
          <span className="terminal-title">A2A PROTOCOL STREAM [JSON-RPC 2.0]</span>
        </div>
        <div className="terminal-tabs">
          <button className={`terminal-tab${activeTermTab === 'stream' ? ' active' : ''}`} onClick={() => setActiveTermTab('stream')}>Live Stream</button>
          <button className={`terminal-tab${activeTermTab === 'rpc' ? ' active' : ''}`} onClick={() => setActiveTermTab('rpc')}>A2A RPC Inspector</button>
          <button className={`terminal-tab${activeTermTab === 'circuit' ? ' active' : ''}`} onClick={() => setActiveTermTab('circuit')}>Circuit Breaker</button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="terminal-filter-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
          <span className="text-dim">Filter:</span>
          <button className="btn btn-ghost" style={{ padding: '2px 6px', fontSize: 10, border: 'none', background: 'var(--surface-container)' }}>All Agents</button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
          <span className={`led ${isRunning ? 'pulse' : ''}`} style={{ background: isRunning ? 'var(--tertiary-fixed)' : 'var(--outline)', width: 8, height: 8 }}></span>
          <span style={{ color: isRunning ? 'var(--tertiary-fixed)' : 'var(--outline)' }}>{isRunning ? 'WEBSOCKET: LIVE' : 'IDLE'}</span>
          <span className="text-dim" style={{ marginLeft: 'var(--space-sm)' }}>|</span>
          <button className="btn-icon" onClick={onClear} style={{ fontSize: 10, padding: '2px 4px' }} title="Clear log">
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>delete</span>
          </button>
          <button
            className="btn-icon"
            onClick={() => setAutoScroll(!autoScroll)}
            style={{ fontSize: 10, padding: '2px 4px', color: autoScroll ? 'var(--primary-fixed)' : 'var(--outline)' }}
            title={autoScroll ? 'Auto-scroll ON' : 'Auto-scroll OFF'}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>vertical_align_bottom</span>
          </button>
        </div>
      </div>

      {/* Terminal Body */}
      <div className="terminal-body" ref={containerRef}>
        {filteredEvents.length === 0 ? (
          <div style={{ color: 'var(--outline)', fontStyle: 'italic', padding: 'var(--space-md)', textAlign: 'center' }}>
            Awaiting pipeline events. Click "Trigger Run" to begin autonomous execution.
          </div>
        ) : (
          filteredEvents.map((ev, i) => {
            const agentName = (ev.agent || 'system').toUpperCase();
            const tagClass = getAgentTagClass(ev.agent);
            const isStrategist = agentName.includes('STRATEGIST');
            const dataStr = ev.data ? (typeof ev.data === 'string' ? ev.data : JSON.stringify(ev.data)) : '';

            return (
              <div className={`terminal-line${isStrategist ? ' highlight' : ''}`} key={i}>
                <span className="terminal-timestamp">{formatTimestamp(ev.timestamp)}</span>
                <span className={`terminal-agent-tag ${isStrategist ? 'secondary-container' : tagClass}`}>{agentName}</span>
                <span className="terminal-message">
                  {ev.event && <span className={`badge ${getEventBadge(ev.event)}`} style={{ marginRight: 4 }}>{ev.event.toUpperCase()}</span>}
                  {dataStr}
                </span>
              </div>
            );
          })
        )}
      </div>

      {/* Command Line */}
      <div className="terminal-command-line">
        <span className="terminal-prompt">$ scrybe --</span>
        <input
          className="terminal-input"
          placeholder="inject rpc://analyst/re-parse --target=anthropic --force-tier3"
          type="text"
        />
        <button className="btn btn-secondary" style={{ padding: '4px var(--space-sm)' }}>Send</button>
      </div>
    </div>
  );
}
