import React from 'react';
import { 
  Shield, 
  BookOpen, 
  Brain, 
  Database, 
  Lightbulb, 
  FileText, 
  ArrowRight, 
  ExternalLink, 
  Zap, 
  Activity,
  Layers,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export default function AgentTopology({ 
  agents = [], 
  agentStates = {}, 
  onSelectAgent,
  activePipelineStage
}) {
  const getAgentIcon = (name) => {
    switch (name.toLowerCase()) {
      case 'compliance': return Shield;
      case 'reader': return BookOpen;
      case 'analyst': return Brain;
      case 'memory': return Database;
      case 'strategist': return Lightbulb;
      case 'formatter': return FileText;
      default: return Activity;
    }
  };

  const getAgentColor = (name) => {
    switch (name.toLowerCase()) {
      case 'compliance': return 'var(--emerald-primary)';
      case 'reader': return 'var(--cyan-primary)';
      case 'analyst': return 'var(--violet-primary)';
      case 'memory': return '#f43f5e';
      case 'strategist': return 'var(--amber-primary)';
      case 'formatter': return '#38bdf8';
      default: return 'var(--text-secondary)';
    }
  };

  // Pipeline execution sequence
  const pipelineFlow = ['reader', 'analyst', 'memory', 'strategist', 'formatter'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Top Banner: Protocol Mesh Overview */}
      <div className="glass-panel" style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(18,24,36,0.9), rgba(12,16,25,0.9))' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Zap size={20} color="var(--cyan-primary)" />
              A2A Agent Topology & Coordination Mesh
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Decoupled autonomous microservice agents communicating exclusively via JSON-RPC 2.0 and Agent Cards.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="badge badge-cyan">
              {agents.length} Registered Agents
            </span>
            <span className="badge badge-violet">
              Decoupled JSON-RPC
            </span>
          </div>
        </div>

        {/* Coordination Workflow Bar */}
        <div style={{
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-md)',
          padding: '16px 20px',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          overflowX: 'auto',
          gap: '12px',
        }}>
          {pipelineFlow.map((stageName, index) => {
            const isCurrent = activePipelineStage === stageName;
            const status = agentStates[stageName] || 'idle';
            const isCompleted = status === 'completed';
            const isWorking = status === 'working' || isCurrent;
            const Icon = getAgentIcon(stageName);

            return (
              <React.Fragment key={stageName}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '8px 14px',
                  borderRadius: 'var(--radius-sm)',
                  background: isWorking 
                    ? 'rgba(0, 240, 255, 0.12)' 
                    : isCompleted 
                    ? 'rgba(16, 185, 129, 0.08)' 
                    : 'transparent',
                  border: `1px solid ${
                    isWorking 
                      ? 'var(--cyan-primary)' 
                      : isCompleted 
                      ? 'rgba(16, 185, 129, 0.3)' 
                      : 'var(--border-subtle)'
                  }`,
                  transition: 'all var(--transition-normal)',
                }}>
                  <div style={{
                    width: '26px',
                    height: '26px',
                    borderRadius: '6px',
                    background: isWorking ? 'var(--cyan-primary)' : 'var(--bg-surface-elevated)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <Icon size={14} color={isWorking ? '#07090e' : getAgentColor(stageName)} />
                  </div>
                  <div>
                    <span style={{ 
                      fontSize: '12px', 
                      fontWeight: 700, 
                      textTransform: 'capitalize',
                      color: isWorking ? 'var(--cyan-primary)' : isCompleted ? 'var(--emerald-primary)' : 'var(--text-primary)'
                    }}>
                      {index + 1}. {stageName}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <div className={`status-dot ${isWorking ? 'working' : isCompleted ? 'active' : 'idle'}`} style={{ width: '5px', height: '5px' }} />
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                        {status}
                      </span>
                    </div>
                  </div>
                </div>

                {index < pipelineFlow.length - 1 && (
                  <ArrowRight size={16} color="var(--text-muted)" style={{ flexShrink: 0 }} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Agent Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '20px',
      }}>
        {agents.map((agent) => {
          const Icon = getAgentIcon(agent.name);
          const color = getAgentColor(agent.name);
          const status = agentStates[agent.name.toLowerCase()] || 'idle';
          const isWorking = status === 'working';

          return (
            <div
              key={agent.name}
              className={`glass-panel ${isWorking ? 'glass-panel-glow' : ''}`}
              onClick={() => onSelectAgent(agent)}
              style={{
                padding: '22px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                cursor: 'pointer',
                position: 'relative',
                overflow: 'hidden',
                background: isWorking ? 'rgba(18, 24, 36, 0.95)' : 'var(--bg-glass)',
              }}
            >
              {/* Top Accent Line */}
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '3px',
                background: isWorking ? 'var(--cyan-primary)' : color,
                opacity: isWorking ? 1 : 0.7,
              }} />

              <div>
                {/* Agent Header */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '42px',
                      height: '42px',
                      borderRadius: '10px',
                      background: 'var(--bg-surface-elevated)',
                      border: `1px solid ${color}44`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}>
                      <Icon size={22} color={color} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '16px', fontWeight: 700, textTransform: 'capitalize', color: 'var(--text-primary)' }}>
                        {agent.name}
                      </h3>
                      <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        {agent.url?.replace('http://', '')}
                      </span>
                    </div>
                  </div>

                  {/* Status Indicator */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-full)',
                    background: isWorking 
                      ? 'rgba(0, 240, 255, 0.1)' 
                      : status === 'completed' 
                      ? 'rgba(16, 185, 129, 0.1)' 
                      : 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '11px',
                    fontWeight: 600,
                  }}>
                    <div className={`status-dot ${isWorking ? 'working' : status === 'completed' ? 'active' : 'idle'}`} />
                    <span style={{ textTransform: 'uppercase', color: isWorking ? 'var(--cyan-primary)' : 'var(--text-secondary)' }}>
                      {status}
                    </span>
                  </div>
                </div>

                {/* Description snippet */}
                <p style={{
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.5,
                  marginBottom: '16px',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                }}>
                  {agent.description}
                </p>

                {/* Skills Preview */}
                <div style={{ marginBottom: '18px' }}>
                  <div style={{ fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Registered Skills ({agent.skills?.length || 0})
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                    {(agent.skills || []).slice(0, 3).map((skill, sIdx) => (
                      <span
                        key={sIdx}
                        style={{
                          fontSize: '11px',
                          background: 'var(--bg-secondary)',
                          color: 'var(--text-secondary)',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          border: '1px solid var(--border-subtle)',
                        }}
                      >
                        {skill.name}
                      </span>
                    ))}
                    {(agent.skills?.length || 0) > 3 && (
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', padding: '2px 4px' }}>
                        +{agent.skills.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Card Footer */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingTop: '12px',
                borderTop: '1px solid var(--border-subtle)',
                fontSize: '11px',
                color: 'var(--cyan-primary)',
              }}>
                <span style={{ color: 'var(--text-muted)' }}>
                  A2A JSON-RPC 2.0
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                  View Agent Card <ExternalLink size={12} />
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
