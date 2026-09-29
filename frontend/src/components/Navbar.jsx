import React from 'react';
import { 
  Bot, 
  Activity, 
  Play, 
  RefreshCw, 
  ShieldCheck, 
  Layers, 
  FileText, 
  BarChart3, 
  SlidersHorizontal,
  Wifi,
  WifiOff
} from 'lucide-react';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  wsConnected, 
  isRunning, 
  onTriggerPipeline,
  pipelineMode,
  setPipelineMode
}) {
  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 50,
      background: 'rgba(7, 9, 14, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '12px 28px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '20px',
    }}>
      {/* Brand & Protocol Tag */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, var(--cyan-primary), var(--violet-primary))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 16px rgba(0, 240, 255, 0.35)',
        }}>
          <Bot size={22} color="#07090e" strokeWidth={2.5} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ 
              fontWeight: 800, 
              fontSize: '18px', 
              letterSpacing: '-0.5px',
              background: 'linear-gradient(90deg, #ffffff 40%, var(--cyan-primary))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              SCRYBE
            </span>
            <span className="badge badge-cyan" style={{ fontSize: '10px', padding: '2px 7px' }}>
              A2A v1.0
            </span>
          </div>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', letterSpacing: '0.2px' }}>
            Autonomous Multi-Agent Intelligence Mesh
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav style={{
        display: 'flex',
        alignItems: 'center',
        background: 'var(--bg-surface)',
        padding: '4px',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        gap: '4px',
      }}>
        {[
          { id: 'topology', label: 'Agent Mesh', icon: Bot },
          { id: 'matrix', label: 'Pricing Matrix', icon: BarChart3 },
          { id: 'strategy', label: 'Strategic Intel', icon: Layers },
          { id: 'compliance', label: 'Compliance Ledger', icon: ShieldCheck },
          { id: 'reports', label: 'Reports', icon: FileText },
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '7px 14px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? 'var(--cyan-primary)' : 'var(--text-secondary)',
                background: isActive ? 'var(--bg-surface-elevated)' : 'transparent',
                boxShadow: isActive ? 'var(--shadow-sm)' : 'none',
                border: isActive ? '1px solid var(--border-medium)' : '1px solid transparent',
                transition: 'all var(--transition-fast)',
              }}
            >
              <Icon size={15} color={isActive ? 'var(--cyan-primary)' : 'var(--text-muted)'} />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Control Area: Mode Selector + WebSocket Indicator + Trigger Button */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Protocol Mode Toggle */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-subtle)',
          padding: '3px 8px',
          gap: '8px',
          fontSize: '11px',
        }}>
          <SlidersHorizontal size={13} color="var(--text-muted)" />
          <span style={{ color: 'var(--text-muted)' }}>Mode:</span>
          <select
            value={pipelineMode}
            onChange={(e) => setPipelineMode(e.target.value)}
            disabled={isRunning}
            style={{
              background: 'transparent',
              color: 'var(--text-primary)',
              border: 'none',
              outline: 'none',
              fontSize: '11px',
              fontWeight: 600,
              cursor: isRunning ? 'not-allowed' : 'pointer',
            }}
          >
            <option value="in_process" style={{ background: '#121824', color: '#fff' }}>
              A2A In-Process
            </option>
            <option value="remote" style={{ background: '#121824', color: '#fff' }}>
              A2A Remote (HTTP)
            </option>
          </select>
        </div>

        {/* WebSocket Connection Status */}
        <div 
          title={wsConnected ? 'WebSocket Live: ws://localhost:8000/ws/pipeline' : 'WebSocket Disconnected: Attempting reconnect'}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '5px 10px',
            borderRadius: 'var(--radius-full)',
            background: wsConnected ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
            border: `1px solid ${wsConnected ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)'}`,
            fontSize: '11px',
            color: wsConnected ? 'var(--emerald-primary)' : 'var(--crimson-primary)',
            fontWeight: 600,
          }}
        >
          {wsConnected ? <Wifi size={13} /> : <WifiOff size={13} />}
          <span>{wsConnected ? 'LIVE FEED' : 'OFFLINE'}</span>
          <div className={`status-dot ${wsConnected ? 'active' : 'error'}`} style={{ width: '6px', height: '6px' }} />
        </div>

        {/* Trigger Pipeline Button */}
        <button
          onClick={onTriggerPipeline}
          disabled={isRunning}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 18px',
            borderRadius: 'var(--radius-md)',
            fontSize: '13px',
            fontWeight: 600,
            color: isRunning ? 'var(--text-muted)' : '#07090e',
            background: isRunning 
              ? 'var(--bg-surface-elevated)' 
              : 'linear-gradient(135deg, var(--cyan-primary), #38bdf8)',
            boxShadow: isRunning ? 'none' : '0 0 16px rgba(0, 240, 255, 0.35)',
            cursor: isRunning ? 'not-allowed' : 'pointer',
            transition: 'all var(--transition-fast)',
          }}
        >
          {isRunning ? (
            <>
              <RefreshCw size={15} style={{ animation: 'radar-scan 1s linear infinite' }} />
              Executing Mesh...
            </>
          ) : (
            <>
              <Play size={15} fill="#07090e" />
              Run A2A Pipeline
            </>
          )}
        </button>
      </div>
    </header>
  );
}
