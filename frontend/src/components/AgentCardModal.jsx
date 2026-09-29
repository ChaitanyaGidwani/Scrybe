import React from 'react';
import { X, Shield, BookOpen, Brain, Database, Lightbulb, FileText, CheckCircle2, Cpu, Terminal } from 'lucide-react';

export default function AgentCardModal({ agent, onClose }) {
  if (!agent) return null;

  const getAgentIcon = (name) => {
    switch (name.toLowerCase()) {
      case 'compliance': return Shield;
      case 'reader': return BookOpen;
      case 'analyst': return Brain;
      case 'memory': return Database;
      case 'strategist': return Lightbulb;
      case 'formatter': return FileText;
      default: return Cpu;
    }
  };

  const Icon = getAgentIcon(agent.name);

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 100,
      background: 'rgba(7, 9, 14, 0.8)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
    }}>
      <div 
        className="glass-panel"
        style={{
          width: '680px',
          maxWidth: '100%',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-accent)',
          boxShadow: 'var(--shadow-lg), 0 0 30px rgba(0, 240, 255, 0.15)',
          overflow: 'hidden',
          borderRadius: 'var(--radius-lg)',
        }}
      >
        {/* Header */}
        <div style={{
          padding: '18px 24px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--bg-surface-elevated)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: 'rgba(0, 240, 255, 0.12)',
              border: '1px solid rgba(0, 240, 255, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Icon size={22} color="var(--cyan-primary)" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 700, textTransform: 'capitalize' }}>
                  {agent.name} Agent
                </h3>
                <span className="badge badge-cyan" style={{ fontSize: '10px' }}>
                  {agent.protocol_version || 'A2A/1.0'}
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Endpoint: {agent.url}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              color: 'var(--text-muted)',
              padding: '6px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Scrollable Content */}
        <div style={{ padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Description */}
          <div>
            <h4 style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--text-muted)', marginBottom: '8px' }}>
              Agent Purpose & Role
            </h4>
            <p style={{ fontSize: '14px', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
              {agent.description}
            </p>
          </div>

          {/* Capabilities */}
          <div>
            <h4 style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--text-muted)', marginBottom: '8px' }}>
              Capabilities & Interface
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              <span className="badge badge-violet">
                JSON-RPC 2.0
              </span>
              <span className="badge badge-emerald">
                Streaming: {agent.capabilities?.streaming ? 'Supported' : 'Standard'}
              </span>
              <span className="badge badge-cyan">
                Stateful Tasks
              </span>
              <span className="badge badge-amber">
                Input/Output Artifacts
              </span>
            </div>
          </div>

          {/* Skills */}
          <div>
            <h4 style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--text-muted)', marginBottom: '10px' }}>
              Registered A2A Skills ({agent.skills?.length || 0})
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {(agent.skills || []).map((skill, idx) => (
                <div 
                  key={idx}
                  style={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '12px 16px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)' }}>
                      {skill.name}
                    </span>
                    <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--cyan-primary)' }}>
                      id: {skill.id}
                    </span>
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                    {skill.description}
                  </p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {(skill.tags || []).map((tag, tIdx) => (
                      <span key={tIdx} style={{
                        fontSize: '10px',
                        background: 'rgba(255, 255, 255, 0.05)',
                        color: 'var(--text-muted)',
                        padding: '2px 6px',
                        borderRadius: '4px',
                      }}>
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sample JSON-RPC Message */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Terminal size={14} color="var(--cyan-primary)" />
              <h4 style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--text-muted)' }}>
                A2A JSON-RPC 2.0 Interaction Spec
              </h4>
            </div>
            <pre style={{
              background: '#090c13',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '14px',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              color: '#38bdf8',
              overflowX: 'auto',
              lineHeight: 1.5,
            }}>
{JSON.stringify({
  jsonrpc: "2.0",
  id: "req_demo_001",
  method: "agent/sendMessage",
  params: {
    message: {
      role: "user",
      parts: [
        {
          type: "data",
          data: { action: agent.skills?.[0]?.id || "execute" }
        }
      ]
    }
  }
}, null, 2)}
            </pre>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'flex-end',
          background: 'var(--bg-surface-elevated)',
        }}>
          <button
            onClick={onClose}
            style={{
              padding: '7px 18px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-medium)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-primary)',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            Close Agent Card
          </button>
        </div>
      </div>
    </div>
  );
}
