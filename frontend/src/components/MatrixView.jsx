import React, { useState } from 'react';
import { Search, ExternalLink, ShieldCheck, AlertCircle, Download, CheckCircle2, DollarSign, Layers } from 'lucide-react';

export default function MatrixView({ records = [], pipelineId = null, onRefresh }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCompany, setSelectedCompany] = useState('all');

  const companies = Array.from(new Set(records.map(r => r.company_name).filter(Boolean)));

  const filteredRecords = records.filter(r => {
    const matchesSearch = 
      (r.company_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (r.product_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (r.citation_text || '').toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCompany = selectedCompany === 'all' || r.company_name === selectedCompany;

    return matchesSearch && matchesCompany;
  });

  const getConfidenceBadge = (confidence) => {
    const score = Number(confidence || 0);
    if (score >= 0.85) {
      return (
        <span className="badge badge-emerald" title="High Grounding Confidence (>= 85%)">
          <CheckCircle2 size={11} /> {(score * 100).toFixed(0)}%
        </span>
      );
    }
    if (score >= 0.70) {
      return (
        <span className="badge badge-amber" title="Moderate Confidence (70-84%)">
          {(score * 100).toFixed(0)}%
        </span>
      );
    }
    return (
      <span className="badge badge-crimson" title="Low Confidence / Flagged (< 70%)">
        <AlertCircle size={11} /> {(score * 100).toFixed(0)}%
      </span>
    );
  };

  const handleExportJson = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(filteredRecords, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `scrybe_pricing_matrix_${pipelineId || 'latest'}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Control & Search Bar */}
      <div className="glass-panel" style={{ padding: '18px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <DollarSign size={20} color="var(--cyan-primary)" />
            Competitor Pricing & Tier Matrix
          </h2>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Zero-hallucination structured records extracted from raw web DOMs with Reflexion self-correction.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Search Input */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '6px 12px',
            gap: '8px',
          }}>
            <Search size={14} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search competitor, model..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: 'var(--text-primary)',
                fontSize: '12px',
                width: '180px',
              }}
            />
          </div>

          {/* Company Filter Dropdown */}
          <select
            value={selectedCompany}
            onChange={(e) => setSelectedCompany(e.target.value)}
            style={{
              background: 'var(--bg-secondary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 12px',
              fontSize: '12px',
              outline: 'none',
            }}
          >
            <option value="all">All Competitors ({records.length})</option>
            {companies.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          {/* Export JSON Button */}
          <button
            onClick={handleExportJson}
            disabled={filteredRecords.length === 0}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-medium)',
              color: 'var(--text-primary)',
              padding: '6px 14px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <Download size={13} /> Export JSON
          </button>
        </div>
      </div>

      {/* Pricing Matrix Records Table / Cards */}
      {filteredRecords.length === 0 ? (
        <div className="glass-panel" style={{ padding: '60px 20px', textAlign: 'center' }}>
          <Layers size={36} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
            No pricing records found
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Run the A2A pipeline to ingest and extract competitor pricing data.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {filteredRecords.map((record, idx) => (
            <div 
              key={idx}
              className="glass-panel"
              style={{
                padding: '20px 24px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px',
              }}
            >
              {/* Record Header */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: '8px',
                    background: 'rgba(0, 240, 255, 0.1)',
                    border: '1px solid rgba(0, 240, 255, 0.25)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    color: 'var(--cyan-primary)',
                    fontSize: '14px',
                  }}>
                    {record.company_name?.charAt(0) || 'C'}
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <h3 style={{ fontSize: '16px', fontWeight: 700 }}>
                        {record.company_name}
                      </h3>
                      <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                        / {record.product_name || 'Standard API'}
                      </span>
                      {record.enterprise_terms_mentioned && (
                        <span className="badge badge-violet" style={{ fontSize: '10px' }}>
                          Enterprise Custom
                        </span>
                      )}
                    </div>
                    {record.source_url && (
                      <a 
                        href={record.source_url} 
                        target="_blank" 
                        rel="noreferrer" 
                        style={{ fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}
                      >
                        {record.source_url} <ExternalLink size={10} />
                      </a>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Confidence Score:
                  </span>
                  {getConfidenceBadge(record.extraction_confidence)}
                </div>
              </div>

              {/* Tiers Grid */}
              <div style={{
                background: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                overflowX: 'auto',
              }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>
                      <th style={{ padding: '10px 14px' }}>Model / Tier</th>
                      <th style={{ padding: '10px 14px' }}>Input Price / 1M Tokens</th>
                      <th style={{ padding: '10px 14px' }}>Output Price / 1M Tokens</th>
                      <th style={{ padding: '10px 14px' }}>Base Monthly Fee</th>
                      <th style={{ padding: '10px 14px' }}>Seat Fee</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(record.pricing_tiers || []).length === 0 ? (
                      <tr>
                        <td colSpan={5} style={{ padding: '14px', textAlign: 'center', color: 'var(--text-muted)' }}>
                          No individual pricing tiers listed.
                        </td>
                      </tr>
                    ) : (
                      (record.pricing_tiers || []).map((tier, tIdx) => (
                        <tr key={tIdx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)' }}>
                          <td style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                            {tier.model_or_tier_name || 'Standard Tier'}
                          </td>
                          <td style={{ padding: '10px 14px', fontFamily: 'var(--font-mono)', color: 'var(--cyan-primary)' }}>
                            {tier.input_price_per_m_tokens != null ? `$${tier.input_price_per_m_tokens.toFixed(2)}` : '—'}
                          </td>
                          <td style={{ padding: '10px 14px', fontFamily: 'var(--font-mono)', color: 'var(--cyan-primary)' }}>
                            {tier.output_price_per_m_tokens != null ? `$${tier.output_price_per_m_tokens.toFixed(2)}` : '—'}
                          </td>
                          <td style={{ padding: '10px 14px', fontFamily: 'var(--font-mono)' }}>
                            {tier.base_price_monthly != null ? `$${tier.base_price_monthly}/mo` : '—'}
                          </td>
                          <td style={{ padding: '10px 14px', fontFamily: 'var(--font-mono)' }}>
                            {tier.seat_price_monthly != null ? `$${tier.seat_price_monthly}/user` : '—'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Citations & Evidence */}
              {record.citation_text && (
                <div style={{
                  padding: '10px 14px',
                  background: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: 'var(--radius-sm)',
                  borderLeft: '3px solid var(--cyan-primary)',
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  fontStyle: 'italic',
                }}>
                  "{record.citation_text}"
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
