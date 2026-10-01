import React, { useState, useEffect, useRef, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import TopHeader from './components/TopHeader';
import DashboardView from './components/DashboardView';
import MatrixView from './components/MatrixView';
import StrategicView from './components/StrategicView';
import ReportsView from './components/ReportsView';
import CompetitorsView from './components/CompetitorsView';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isRunning, setIsRunning] = useState(false);
  const [activePipelineStage, setActivePipelineStage] = useState(null);
  const [currentPipelineId, setCurrentPipelineId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [lastUpdated, setLastUpdated] = useState('Live');

  // Core Data Stores
  const [matrixRecords, setMatrixRecords] = useState([]);
  const [strategicInsights, setStrategicInsights] = useState([]);
  const [reports, setReports] = useState([]);
  const [pipelineEvents, setPipelineEvents] = useState([]);

  // WebSocket Connection
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // Fetch initial data from backend
  const fetchAllData = useCallback(async () => {
    try {
      // 1. Fetch Pricing Matrix
      const matrixRes = await fetch('/api/v1/matrix');
      if (matrixRes.ok) {
        const data = await matrixRes.json();
        setMatrixRecords(data.competitors || []);
        if (data.pipeline_id) setCurrentPipelineId(data.pipeline_id);
      }

      // 2. Fetch Strategic Insights
      const insightsRes = await fetch('/api/v1/insights');
      if (insightsRes.ok) {
        const data = await insightsRes.json();
        setStrategicInsights(data.insights || []);
      }

      // 3. Fetch Reports
      const reportsRes = await fetch('/api/v1/reports');
      if (reportsRes.ok) {
        const data = await reportsRes.json();
        setReports(data.reports || []);
      }

      // 4. Fetch Recent Progress Events
      const eventsRes = await fetch('/api/v1/a2a/progress');
      if (eventsRes.ok) {
        const data = await eventsRes.json();
        if (data.events && data.events.length > 0) {
          setPipelineEvents(data.events);
        }
      }

      const now = new Date();
      setLastUpdated(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
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

            setPipelineEvents((prev) => [...prev.slice(-100), msg]);

            const agentName = (msg.agent || '').toLowerCase();
            const eventType = (msg.event || '').toLowerCase();

            if (msg.pipeline_id) {
              setCurrentPipelineId(msg.pipeline_id);
            }

            if (eventType === 'starting' || eventType === 'working') {
              setActivePipelineStage(agentName);
              setIsRunning(true);
            } else if (eventType === 'completed') {
              if (agentName === 'pipeline' || agentName === 'formatter') {
                setIsRunning(false);
                setActivePipelineStage(null);
                setTimeout(fetchAllData, 1000);
              }
            } else if (eventType === 'failed') {
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

        socket.onerror = () => {
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

  // Trigger On-Demand Market Scan
  const handleTriggerScan = async () => {
    setIsRunning(true);
    setActivePipelineStage('reader');

    const initialEvent = {
      pipeline_id: 'scan-init',
      agent: 'reader',
      event: 'starting',
      timestamp: new Date().toISOString(),
      data: { message: 'Initiating real-time competitor scan...' },
    };
    setPipelineEvents((prev) => [...prev, initialEvent]);

    try {
      const response = await fetch('/api/v1/a2a/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'in_process' }),
      });

      if (!response.ok) {
        throw new Error(`Failed to start scan: ${response.statusText}`);
      }

      const resData = await response.json();
      setCurrentPipelineId(resData.pipeline_id);
    } catch (err) {
      console.error('Market scan trigger failed:', err);
      setIsRunning(false);
      setActivePipelineStage(null);
    }
  };

  // Global Export CSV from Top Header
  const handleExportCSV = () => {
    const rows = [];
    (matrixRecords || []).forEach((rec) => {
      const company = rec.company_name || 'Unknown';
      const product = rec.product_name || '';
      (rec.pricing_tiers || []).forEach((t) => {
        rows.push([
          `"${company}"`,
          `"${product}"`,
          `"${t.model_name || t.tier_name || ''}"`,
          t.input_price_per_1m != null ? t.input_price_per_1m : '',
          t.output_price_per_1m != null ? t.output_price_per_1m : '',
          t.cache_price_per_1m != null ? t.cache_price_per_1m : '',
          t.context_window || '',
        ]);
      });
    });

    if (rows.length === 0) {
      alert('No pricing data available to export yet. Please run a market scan first.');
      return;
    }

    const headers = ['Company', 'Product', 'Model', 'Input Price ($/1M)', 'Output Price ($/1M)', 'Cache Price ($/1M)', 'Context Window'];
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scrybe_pricing_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="app-shell">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        wsConnected={wsConnected}
        isRunning={isRunning}
      />

      {/* Main Content Area */}
      <div className="main-area">
        {/* Top Header */}
        <TopHeader
          activeTab={activeTab}
          wsConnected={wsConnected}
          isRunning={isRunning}
          onTriggerScan={handleTriggerScan}
          lastUpdated={lastUpdated}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          onExport={handleExportCSV}
        />

        {/* Dynamic Page Views */}
        <main className="page-content">
          {activeTab === 'dashboard' && (
            <DashboardView
              records={matrixRecords}
              insights={strategicInsights}
              reports={reports}
              isRunning={isRunning}
              activePipelineStage={activePipelineStage}
              onTriggerScan={handleTriggerScan}
              setActiveTab={setActiveTab}
              pipelineEvents={pipelineEvents}
            />
          )}

          {activeTab === 'matrix' && (
            <MatrixView
              records={matrixRecords}
              onRefresh={fetchAllData}
              searchQuery={searchQuery}
            />
          )}

          {activeTab === 'strategy' && (
            <StrategicView
              insights={strategicInsights}
              records={matrixRecords}
            />
          )}

          {activeTab === 'reports' && (
            <ReportsView
              reports={reports}
            />
          )}

          {activeTab === 'competitors' && (
            <CompetitorsView
              records={matrixRecords}
            />
          )}
        </main>
      </div>
    </div>
  );
}
