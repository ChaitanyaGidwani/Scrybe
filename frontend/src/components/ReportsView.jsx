import React, { useState, useEffect } from 'react';
import { FileText, Download, Calendar, ExternalLink, ChevronRight, BookOpen, CheckCircle } from 'lucide-react';

export default function ReportsView({ reports = [], onSelectReport, selectedReport }) {
  const [activeReportId, setActiveReportId] = useState(reports[0]?.report_id || null);
  const [reportDetail, setReportDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (reports.length > 0 && !activeReportId) {
      setActiveReportId(reports[0].report_id);
    }
  }, [reports]);

  useEffect(() => {
    if (!activeReportId) return;
    setLoading(true);
    fetch(`/api/v1/reports/${activeReportId}`)
      .then(res => res.json())
      .then(data => {
        setReportDetail(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load report:', err);
        setLoading(false);
      });
  }, [activeReportId]);

  const handleDownloadMarkdown = () => {
    if (!reportDetail?.markdown_content) return;
    const blob = new Blob([reportDetail.markdown_content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${reportDetail.report_id || 'scrybe_report'}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px' }}>
      {/* Sidebar: Reports List */}
      <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px', height: 'fit-content' }}>
        <div style={{ padding: '8px 10px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={16} color="var(--cyan-primary)" />
          <h3 style={{ fontSize: '14px', fontWeight: 700 }}>
            Reports Archive ({reports.length})
          </h3>
        </div>

        {reports.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
            No reports generated yet.
          </div>
        ) : (
          reports.map((rpt) => {
            const isSelected = rpt.report_id === activeReportId;
            return (
              <div
                key={rpt.report_id}
                onClick={() => setActiveReportId(rpt.report_id)}
                style={{
                  padding: '12px 14px',
                  borderRadius: 'var(--radius-sm)',
                  background: isSelected ? 'var(--bg-surface-elevated)' : 'var(--bg-secondary)',
                  border: `1px solid ${isSelected ? 'var(--cyan-primary)' : 'var(--border-subtle)'}`,
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: isSelected ? 'var(--cyan-primary)' : 'var(--text-primary)' }}>
                    {rpt.title || 'Market Intelligence Brief'}
                  </span>
                  <ChevronRight size={14} color={isSelected ? 'var(--cyan-primary)' : 'var(--text-muted)'} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <Calendar size={11} />
                  <span>{rpt.generated_at ? new Date(rpt.generated_at).toLocaleDateString() : 'Recent'}</span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Main Content: Report Viewer */}
      <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {loading ? (
          <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading report payload...
          </div>
        ) : !reportDetail ? (
          <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Select a report from the archive to inspect markdown and citations.
          </div>
        ) : (
          <>
            {/* Report Header */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '18px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span className="badge badge-cyan" style={{ fontSize: '10px' }}>
                    {reportDetail.target_vertical || 'B2B AI PLATFORMS'}
                  </span>
                  <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    ID: {reportDetail.report_id}
                  </span>
                </div>
                <h2 style={{ fontSize: '22px', fontWeight: 800 }}>
                  {reportDetail.title}
                </h2>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Generated on {reportDetail.generated_at ? new Date(reportDetail.generated_at).toLocaleString() : 'N/A'} via A2A FormatterAgent
                </p>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={handleDownloadMarkdown}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-surface-elevated)',
                    border: '1px solid var(--border-medium)',
                    color: 'var(--text-primary)',
                    fontSize: '12px',
                    fontWeight: 600,
                  }}
                >
                  <Download size={14} /> Download Markdown (.md)
                </button>
              </div>
            </div>

            {/* Executive Summary Callout */}
            {reportDetail.executive_summary && (
              <div style={{
                background: 'rgba(0, 240, 255, 0.04)',
                borderLeft: '4px solid var(--cyan-primary)',
                padding: '16px 20px',
                borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
              }}>
                <h4 style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--cyan-primary)', fontWeight: 700, letterSpacing: '0.6px', marginBottom: '6px' }}>
                  Executive Summary
                </h4>
                <p style={{ fontSize: '14px', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
                  {reportDetail.executive_summary}
                </p>
              </div>
            )}

            {/* Markdown Body */}
            <div>
              <h4 style={{ fontSize: '13px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.6px', marginBottom: '12px' }}>
                Full Synthesized Intelligence Brief
              </h4>
              <div style={{
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '24px',
                fontFamily: 'var(--font-sans)',
                fontSize: '13px',
                lineHeight: 1.7,
                color: 'var(--text-primary)',
                maxHeight: '450px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
              }}>
                {reportDetail.markdown_content || 'No markdown content available.'}
              </div>
            </div>

            {/* Grounded Citations Section */}
            {reportDetail.citations && (
              <div>
                <h4 style={{ fontSize: '13px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.6px', marginBottom: '10px' }}>
                  Grounded Evidence Citations
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {(typeof reportDetail.citations === 'string' 
                    ? JSON.parse(reportDetail.citations || '[]') 
                    : reportDetail.citations
                  ).map((cite, cIdx) => (
                    <div key={cIdx} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px 14px',
                      background: 'var(--bg-secondary)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '12px',
                    }}>
                      <CheckCircle size={14} color="var(--emerald-primary)" />
                      <span style={{ color: 'var(--text-secondary)' }}>
                        {typeof cite === 'string' ? cite : cite.text || cite.url}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
