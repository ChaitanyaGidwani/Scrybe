import React, { useState, useEffect, useRef, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import TopHeader from './components/TopHeader';
import TelemetryRibbon from './components/TelemetryRibbon';
import AgentTopology from './components/AgentTopology';
import PipelineTerminal from './components/PipelineTerminal';
import DeltaAlerts from './components/DeltaAlerts';
import MatrixView from './components/MatrixView';
import StrategicView from './components/StrategicView';
import ComplianceLedger from './components/ComplianceLedger';
import ReportsView from './components/ReportsView';
import AgentCardModal from './components/AgentCardModal';

export default function App() {
  const [activeTab, setActiveTab] = useState('topology');
  const [pipelineMode, setPipelineMode] = useState('in_process');
  const [isRunning, setIsRunning] = useState(false);
  const [activePipelineStage, setActivePipelineStage] = useState(null);
  const [currentPipelineId, setCurrentPipelineId] = useState(null);

  // A2A Agents & States
  const [agents, setAgents] = useState([]);
  const [agentStates, setAgentStates] = useState({});
  const [selectedAgentModal, setSelectedAgentModal] = useState(null);

  // Data Stores
  const [pipelineEvents, setPipelineEvents] = useState([]);
  const [matrixRecords, setMatrixRecords] = useState([]);
  const [strategicInsights, setStrategicInsights] = useState([]);
  const [complianceAudits, setComplianceAudits] = useState([]);
  const [reports, setReports] = useState([]);

  // WebSocket Connection
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // Fetch initial data from FastAPI backend
  const fetchAllData = useCallback(async () => {
    try {
      // 1. Fetch Agents
      const agentsRes = await fetch('/api/v1/agents');
      if (agentsRes.ok) {
        const data = await agentsRes.json();
        setAgents(data.agents || []);
      }

      // 2. Fetch Pricing Matrix
      const matrixRes = await fetch('/api/v1/matrix');
      if (matrixRes.ok) {
        const data = await matrixRes.json();
        setMatrixRecords(data.competitors || []);
        if (data.pipeline_id) setCurrentPipelineId(data.pipeline_id);
      }

      // 3. Fetch Strategic Insights
      const insightsRes = await fetch('/api/v1/insights');
      if (insightsRes.ok) {
        const data = await insightsRes.json();
        setStrategicInsights(data.insights || []);
      }

      // 4. Fetch Compliance Audits
      const auditsRes = await fetch('/api/v1/audits');
      if (auditsRes.ok) {
        const data = await auditsRes.json();
        setComplianceAudits(data.audits || []);
      }

      // 5. Fetch Reports
      const reportsRes = await fetch('/api/v1/reports');
      if (reportsRes.ok) {
        const data = await reportsRes.json();
        setReports(data.reports || []);
      }

      // 6. Fetch Recent Events
      const eventsRes = await fetch('/api/v1/a2a/progress');
      if (eventsRes.ok) {
        const data = await eventsRes.json();
        if (data.events && data.events.length > 0) {
          setPipelineEvents(data.events);
        }
      }
    } catch (err) {
      console.warn('Backend not fully reachable yet:', err);
    }
  }, []);

  // WebSocket lifecycle management
  useEffect(() => {
    fetchAllData();

    function connectWebSocket() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/pipeline`;

      try {
        const socket = new WebSocket(wsUrl);
        wsRef.current = socket;

        socket.onopen = () => {
          setWsConnected(true);
        };

        socket.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'pong') return;

            setPipelineEvents(prev => [...prev.slice(-300), msg]);

            const agentName = (msg.agent || '').toLowerCase();
            const eventType = (msg.event || '').toLowerCase();

            if (msg.pipeline_id) {
              setCurrentPipelineId(msg.pipeline_id);
            }

            if (eventType === 'starting' || eventType === 'working') {
              setActivePipelineStage(agentName);
              setAgentStates(prev => ({ ...prev, [agentName]: 'working' }));
              setIsRunning(true);
            } else if (eventType === 'completed') {
              setAgentStates(prev => ({ ...prev, [agentName]: 'completed' }));
              if (agentName === 'pipeline' || agentName === 'formatter') {
                setIsRunning(false);
                setActivePipelineStage(null);
                setTimeout(fetchAllData, 1000);
              }
            } else if (eventType === 'failed') {
              setAgentStates(prev => ({ ...prev, [agentName]: 'failed' }));
              if (agentName === 'pipeline') {
                setIsRunning(false);
                setActivePipelineStage(null);
              }
            }
          } catch (e) {
            console.error('Error parsing WS message:', e);
          }
        };

        socket.onclose = () => {
          setWsConnected(false);
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = (err) => {
          setWsConnected(false);
          socket.close();
        };
      } catch (err) {
        setWsConnected(false);
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
      }
    }

    connectWebSocket();

    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping');
      }
    }, 15000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [fetchAllData]);

  // Trigger A2A Pipeline Run
  const handleTriggerPipeline = async () => {
    setIsRunning(true);
    setAgentStates({});
    setActivePipelineStage('reader');

    const initialEvent = {
      pipeline_id: 'pending...',
      agent: 'pipeline',
      event: 'starting',
      timestamp: new Date().toISOString(),
      data: { mode: pipelineMode, triggered_by: 'Dashboard UI' }
    };
    setPipelineEvents(prev => [...prev, initialEvent]);

    try {
      const response = await fetch('/api/v1/a2a/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: pipelineMode }),
      });

      if (!response.ok) {
        throw new Error(`Failed to start pipeline: ${response.statusText}`);
      }

      const resData = await response.json();
      setCurrentPipelineId(resData.pipeline_id);
    } catch (err) {
      console.error('Pipeline run trigger failed:', err);
      setIsRunning(false);
      setActivePipelineStage(null);
      setPipelineEvents(prev => [
        ...prev,
        {
          pipeline_id: 'error',
          agent: 'pipeline',
          event: 'failed',
          timestamp: new Date().toISOString(),
          data: { error: err.message }
        }
      ]);
    }
  };

  return (
    <div className="app-layout">
      {/* Fixed Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        wsConnected={wsConnected}
      />

      {/* Main Content Area (offset by sidebar) */}
      <div className="content-area">
        {/* Fixed Top Header */}
        <TopHeader
          wsConnected={wsConnected}
          isRunning={isRunning}
          onTriggerPipeline={handleTriggerPipeline}
          pipelineMode={pipelineMode}
          setPipelineMode={setPipelineMode}
        />

        {/* Scrollable Main Content */}
        <main className="main-content">
          {/* ── Autonomous Pipeline Tab ─────────────────── */}
          {activeTab === 'topology' && (
            <>
              {/* Telemetry Stat Ribbon */}
              <TelemetryRibbon />

              {/* Agent Swarm Topology */}
              <AgentTopology
                agentStates={agentStates}
                onSelectAgent={setSelectedAgentModal}
                activePipelineStage={activePipelineStage}
              />

              {/* Two Column: Terminal + Delta Alerts */}
              <div className="split-layout">
                <PipelineTerminal
                  events={pipelineEvents}
                  isRunning={isRunning}
                  activeStage={activePipelineStage}
                  pipelineId={currentPipelineId}
                  onClear={() => setPipelineEvents([])}
                />
                <DeltaAlerts
                  insights={strategicInsights}
                />
              </div>
            </>
          )}

          {/* ── Pricing Matrix Tab ──────────────────────── */}
          {activeTab === 'matrix' && (
            <MatrixView
              records={matrixRecords}
              pipelineId={currentPipelineId}
              onRefresh={fetchAllData}
            />
          )}

          {/* ── Executive Intelligence Tab ──────────────── */}
          {activeTab === 'strategy' && (
            <StrategicView
              insights={strategicInsights}
              records={matrixRecords}
            />
          )}

          {/* ── Compliance & Audit Tab ──────────────────── */}
          {activeTab === 'compliance' && (
            <ComplianceLedger
              audits={complianceAudits}
            />
          )}

          {/* ── Reports / A2A Swarm Tab ─────────────────── */}
          {activeTab === 'reports' && (
            <ReportsView
              reports={reports}
            />
          )}
        </main>
      </div>

      {/* Agent Detail Modal */}
      {selectedAgentModal && (
        <AgentCardModal
          agent={selectedAgentModal}
          onClose={() => setSelectedAgentModal(null)}
        />
      )}
    </div>
  );
}
