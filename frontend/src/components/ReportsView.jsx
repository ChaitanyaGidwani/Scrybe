import React from 'react';

export default function ReportsView({ reports }) {
  return (
    <section>
      <div className="card-elevated">
        <div style={{ paddingBottom: 'var(--space-md)' }}>
          <div className="section-header">
            <span className="section-overline">A2A Agent Swarm Output</span>
            <h2 className="section-title" style={{ fontWeight: 700 }}>Generated Reports & Artifacts</h2>
            <p className="section-subtitle">Executive markdown digests, PDF artifacts, and published intelligence briefs from the autonomous pipeline.</p>
          </div>
        </div>

        {reports && reports.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 'var(--space-md)' }}>
            {reports.map((report, i) => (
              <div className="alert-card" key={i} style={{ cursor: 'pointer' }}>
                <div className="alert-gradient-bar green-cyan"></div>
                <div className="alert-header" style={{ paddingTop: 4 }}>
                  <span className="badge badge-green font-bold" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 12 }}>
                      {report.format === 'pdf' ? 'picture_as_pdf' : 'description'}
                    </span>
                    {(report.format || 'MD').toUpperCase()}
                  </span>
                  <span className="text-label-sm text-dim">
                    {report.generated_at ? new Date(report.generated_at).toLocaleDateString() : '—'}
                  </span>
                </div>
                <h4 className="alert-title" style={{ fontSize: 16 }}>
                  {report.title || `Report #${i + 1}`}
                </h4>
                <p className="alert-body" style={{ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {report.summary || report.preview || 'No preview available.'}
                </p>
                <div className="alert-footer">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 14, color: 'var(--tertiary-fixed)' }}>schedule</span>
                    <span>{report.generated_at ? new Date(report.generated_at).toLocaleTimeString('en-US', { hour12: false }) : '—'}</span>
                  </div>
                  {report.pipeline_id && (
                    <span className="badge badge-cyan">{report.pipeline_id}</span>
                  )}
                  {report.download_url && (
                    <a href={report.download_url} className="text-cyan" style={{ display: 'flex', alignItems: 'center', gap: 2 }} target="_blank" rel="noopener noreferrer">
                      <span className="material-symbols-outlined" style={{ fontSize: 14 }}>download</span>
                      Download
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--outline)' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 48, display: 'block', marginBottom: 'var(--space-sm)' }}>feed</span>
            <p className="text-body-lg">No reports generated yet.</p>
            <p className="text-body-sm text-muted">Run the pipeline to produce executive briefs and PDF artifacts.</p>
          </div>
        )}
      </div>
    </section>
  );
}
