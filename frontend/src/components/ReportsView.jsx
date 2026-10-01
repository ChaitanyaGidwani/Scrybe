import React, { useState } from 'react';

const SAMPLE_REPORTS = [
  {
    id: 'rep-01',
    title: 'Q4 AI Model Pricing & Cost Optimization Executive Digest',
    date: 'October 1, 2026',
    format: 'Executive Brief',
    summary:
      'Comprehensive comparative analysis of token rates across OpenAI, Anthropic, Mistral, and Groq. Identifies key margin levers in prompt caching and commodity small-model migration.',
    content: `# Q4 AI Model Pricing & Cost Optimization Executive Digest

## Executive Summary
Over the past quarter, the foundation model market has bifurcated into two distinct economic regimes:
1. **Frontier Reasoning & Coding Tier**: Models like OpenAI o1/GPT-4o and Anthropic Claude 3.5 Sonnet continue to command $2.50 - $3.00/1M input and $10.00 - $15.00/1M output, with differentiation shifting to prompt caching discounts and long-horizon tool execution.
2. **Sub-Dollar Utility Tier**: Small footprint models (GPT-4o mini, Mistral NeMo, Llama 3.1 8B) have dropped to near-zero input cost ($0.15/1M), commoditizing high-frequency triage tasks.

## Key Recommendations
- **Adopt Prompt Caching**: Teams adopting persistent system prompt caching can reduce repetitive pipeline costs by up to 75%.
- **Route Non-Reasoning Tasks**: Re-route data extraction, classification, and summarization from frontier models to mini tiers.
- **Leverage LPU Hardware**: For customer-facing voice and chat applications, evaluate specialized inference engines like Groq to reduce latency by 4x.
`,
  },
  {
    id: 'rep-02',
    title: 'Frontier Long-Context Economics & Token Parity Audit',
    date: 'September 28, 2026',
    format: 'Market Report',
    summary:
      'Detailed audit of context window expansion (128K to 200K+) and its financial impact on retrieval-augmented generation (RAG) vs. raw context injection architectures.',
    content: `# Frontier Long-Context Economics & Token Parity Audit

## Overview
As context windows expand up to 200K tokens across frontier commercial APIs, development teams face a fundamental trade-off: traditional vector database chunking vs. full-document context window ingestion.

## Financial Comparison
- **Vector Search (Pinecone + Embeddings)**: High initial embedding cost, but minimal recurring token expenditure ($0.0001 per retrieval).
- **Direct Context Ingestion**: Zero indexing pipeline complexity, but linear token burn (~$0.60 per 200K token call).

## Conclusion
For dynamic documents that change hourly, full-context window injection is cost-effective. For static knowledge bases (>10M tokens), vector retrieval remains mandatory for margin preservation.
`,
  },
];

export default function ReportsView({ reports }) {
  const [selectedReport, setSelectedReport] = useState(null);

  const displayReports =
    reports && reports.length > 0
      ? reports.map((r, i) => ({
          id: r.id || `rep-${i}`,
          title: r.title || `Executive Report #${i + 1}`,
          date: r.generated_at ? new Date(r.generated_at).toLocaleDateString() : 'Recent',
          format: (r.format || 'Executive Digest').toUpperCase(),
          summary: r.summary || r.preview || 'Executive intelligence digest generated from competitor market data.',
          content: r.content || r.markdown || r.summary || '# Executive Report\n\nNo detailed text content provided.',
          downloadUrl: r.download_url,
        }))
      : SAMPLE_REPORTS;

  return (
    <div className="reports-page">
      <div className="card-header" style={{ marginBottom: 24 }}>
        <div>
          <h2 className="card-title" style={{ fontSize: 20 }}>Executive Market Reports</h2>
          <p className="card-description">
            Published briefings and strategic digests on competitive movements and pricing trends.
          </p>
        </div>
      </div>

      <div className="reports-list">
        {displayReports.map((report) => (
          <div key={report.id} className="report-item">
            <div className="report-info">
              <div className="report-icon-box">
                <span className="material-symbols-outlined">description</span>
              </div>
              <div className="report-meta">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span className="badge badge-purple">{report.format}</span>
                  <span className="report-date">{report.date}</span>
                </div>
                <h3 className="report-title">{report.title}</h3>
                <p className="report-desc">{report.summary}</p>
              </div>
            </div>

            <div className="report-actions">
              <button
                className="btn btn-secondary"
                onClick={() => setSelectedReport(report)}
                type="button"
              >
                <span className="material-symbols-outlined">visibility</span>
                <span>Read Brief</span>
              </button>

              <button
                className="btn btn-secondary btn-icon-only"
                onClick={() => {
                  const blob = new Blob([report.content], { type: 'text/markdown' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${report.title.toLowerCase().replace(/[^a-z0-9]/g, '_')}.md`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                title="Download Markdown Report"
                type="button"
              >
                <span className="material-symbols-outlined">download</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* ── Report Reading Modal ── */}
      {selectedReport && (
        <div className="modal-backdrop" onClick={() => setSelectedReport(null)}>
          <div className="report-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span className="badge badge-purple" style={{ marginBottom: 6 }}>
                  {selectedReport.format}
                </span>
                <h2 className="modal-title">{selectedReport.title}</h2>
                <span className="text-muted" style={{ fontSize: 13 }}>
                  Published on {selectedReport.date}
                </span>
              </div>
              <button
                className="btn-icon"
                onClick={() => setSelectedReport(null)}
                type="button"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <div className="report-modal-body">
              <pre className="report-markdown-preview">{selectedReport.content}</pre>
            </div>

            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={() => setSelectedReport(null)}
                type="button"
              >
                Close
              </button>
              <button
                className="btn btn-primary"
                onClick={() => {
                  const blob = new Blob([selectedReport.content], { type: 'text/markdown' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${selectedReport.title.toLowerCase().replace(/[^a-z0-9]/g, '_')}.md`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                type="button"
              >
                <span className="material-symbols-outlined">download</span>
                <span>Download Report</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
