import React, { useState, useRef, useEffect } from 'react';
import { Terminal, Shield, Play, CheckCircle2, AlertTriangle, ArrowDown, Trash2, Filter, Clock } from 'lucide-react';

export default function PipelineTerminal({ 
  events = [], 
  isRunning = false, 
  activeStage = null,
  pipelineId = null,
  onClear
}) {
  const [filterAgent, setFilterAgent] = useState('all');
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const logEndRef = useRef(null);

  useEffect(() => {
    if (autoScroll && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events, autoScroll]);

  const filteredEvents = events.filter(e => {
    if (filterAgent === 'all') return true;
    return (e.agent || '').toLowerCase() === filterAgent.toLowerCase();
  });

  const getEventBadgeClass = (event) => {
    const ev = (event.event || '').toLowerCase();
    if (ev.includes('complete') || ev.includes('ok') || ev.includes('success')) return 'badge-emerald';
    if (ev.includes('fail') || ev.includes('error') || ev.includes('block')) return 'badge-crimson';
    if (ev.includes('start') || ev.includes('progress') || ev.includes('working')) return 'badge-cyan';
    return 'badge-violet';
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Terminal Header */}
      <div style={{
        padding: '14px 20px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--bg-surface-elevated)',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Terminal size={18} color="var(--cyan-primary)" />
          <span style={{ fontWeight: 700, fontSize: '14px' }}>
            A2A Real-Time Event Stream
          </span>
          {pipelineId && (
            <span style={{ 
              fontFamily: 'var(--font-mono)', 
              fontSize: '11px', 
              color: 'var(--cyan-primary)',
              background: 'rgba(0, 240, 255, 0.08)',
              padding: '2px 8px',
              borderRadius: '4px',
            }}>
              {pipelineId}
            </span>
          )}
          {isRunning && (
            <span className="badge badge-cyan" style={{ fontSize: '10px' }}>
              Streaming Active
            </span>
          )}
        </div>

        {/* Controls: Filter + AutoScroll + Clear */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Filter by Agent */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
            <Filter size={13} color="var(--text-muted)" />
            <select
              value={filterAgent}
              onChange={(e) => setFilterAgent(e.target.value)}
              style={{
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '4px 8px',
                fontSize: '11px',
                outline: 'none',
              }}
            >
              <option value="all">All Agents</option>
              <option value="pipeline">Pipeline</option>
              <option value="compliance">Compliance</option>
              <option value="reader">Reader</option>
              <option value="analyst">Analyst</option>
              <option value="memory">Memory</option>
              <option value="strategist">Strategist</option>
              <option value="formatter">Formatter</option>
            </select>
          </div>

          {/* AutoScroll Toggle */}
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            style={{
              background: autoScroll ? 'rgba(0, 240, 255, 0.12)' : 'var(--bg-secondary)',
              border: `1px solid ${autoScroll ? 'var(--cyan-primary)' : 'var(--border-subtle)'}`,
              color: autoScroll ? 'var(--cyan-primary)' : 'var(--text-muted)',
              padding: '4px 10px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '11px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <ArrowDown size={12} /> AutoScroll
          </button>

          {/* Clear Logs */}
          <button
            onClick={onClear}
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-muted)',
              padding: '4px 8px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '11px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
            title="Clear terminal logs"
          >
            <Trash2 size={12} /> Clear
          </button>
        </div>
      </div>

      {/* Terminal Log Output Window */}
      <div style={{
        height: '280px',
        overflowY: 'auto',
        padding: '12px 18px',
        background: '#07090e',
        fontFamily: 'var(--font-mono)',
        fontSize: '12px',
        lineHeight: 1.6,
      }}>
        {filteredEvents.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px 0', fontSize: '13px' }}>
            No live events received yet. Click "Run A2A Pipeline" to launch autonomous agent coordination.
          </div>
        ) : (
          filteredEvents.map((ev, index) => {
            const timeStr = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '--:--:--';
            return (
              <div 
                key={index}
                onClick={() => setSelectedEvent(ev)}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '4px 0',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                  cursor: 'pointer',
                  transition: 'background var(--transition-fast)',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <span style={{ color: 'var(--text-muted)', flexShrink: 0, fontSize: '11px' }}>
                  [{timeStr}]
                </span>

                <span style={{ 
                  color: 'var(--cyan-primary)', 
                  fontWeight: 600, 
                  textTransform: 'uppercase',
                  minWidth: '90px',
                  flexShrink: 0,
                  fontSize: '11px',
                }}>
                  {ev.agent || 'SYSTEM'}
                </span>

                <span className={`badge ${getEventBadgeClass(ev)}`} style={{ fontSize: '9px', padding: '1px 6px', flexShrink: 0 }}>
                  {ev.event || 'INFO'}
                </span>

                <span style={{ color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {ev.data ? JSON.stringify(ev.data) : ev.message || 'Stage event triggered'}
                </span>
              </div>
            );
          })
        )}
        <div ref={logEndRef} />
      </div>

      {/* JSON Payload Inspector Drawer (When clicked) */}
      {selectedEvent && (
        <div style={{
          padding: '12px 18px',
          background: 'var(--bg-secondary)',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--cyan-primary)', textTransform: 'uppercase' }}>
              A2A Event Inspector — {selectedEvent.agent} :: {selectedEvent.event}
            </span>
            <button 
              onClick={() => setSelectedEvent(null)}
              style={{ background: 'transparent', color: 'var(--text-muted)', fontSize: '11px' }}
            >
              Close Inspector
            </button>
          </div>
          <pre style={{
            background: '#05070a',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            color: '#38bdf8',
            maxHeight: '140px',
            overflowY: 'auto',
          }}>
            {JSON.stringify(selectedEvent, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
