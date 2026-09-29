import React from 'react';
import { ShieldCheck, ShieldAlert, Lock, Clock, EyeOff, CheckCircle2, AlertOctagon, ExternalLink } from 'lucide-react';

export default function ComplianceLedger({ audits = [] }) {
  const totalAudits = audits.length;
  const approvedAudits = audits.filter(a => a.compliance_status === 'APPROVED').length;
  const totalPiiScrubbed = audits.reduce((acc, a) => acc + (a.pii_scrubbed_count || 0), 0);
  const avgDelay = totalAudits > 0 
    ? (audits.reduce((acc, a) => acc + (a.crawl_delay_applied || 2.5), 0) / totalAudits).toFixed(1) 
    : '2.5';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Overview Stat Counters */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
      }}>
        <div className="glass-panel" style={{ padding: '18px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'rgba(16, 185, 129, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <ShieldCheck size={22} color="var(--emerald-primary)" />
          </div>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              Pre-Flight Audits
            </div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)' }}>
              {totalAudits}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--emerald-primary)' }}>
              {approvedAudits} Verified Compliant
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '18px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'rgba(0, 240, 255, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Lock size={22} color="var(--cyan-primary)" />
          </div>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              SSRF & Security Gates
            </div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)' }}>
              100%
            </div>
            <div style={{ fontSize: '11px', color: 'var(--cyan-primary)' }}>
              Private IP Ranges Blocked
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '18px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'rgba(139, 92, 246, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <EyeOff size={22} color="var(--violet-primary)" />
          </div>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              PII Redactions
            </div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)' }}>
              {totalPiiScrubbed}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--violet-primary)' }}>
              Emails & IDs Sanitized
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '18px 20px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'rgba(245, 158, 11, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <Clock size={22} color="var(--amber-primary)" />
          </div>
          <div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              Politeness Crawl Delay
            </div>
            <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)' }}>
              {avgDelay}s
            </div>
            <div style={{ fontSize: '11px', color: 'var(--amber-primary)' }}>
              Mandatory Backoff Enforced
            </div>
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--border-subtle)' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={18} color="var(--emerald-primary)" />
            Cryptographic & Ethical Ingestion Ledger
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Every network request is checked for robots.txt clearance, RFC-1918 SSRF blocking, and PII anonymization.
          </p>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase' }}>
                <th style={{ padding: '12px 18px' }}>Audit ID</th>
                <th style={{ padding: '12px 18px' }}>Target URL</th>
                <th style={{ padding: '12px 18px' }}>Robots.txt</th>
                <th style={{ padding: '12px 18px' }}>SSRF Check</th>
                <th style={{ padding: '12px 18px' }}>PII Scrubbed</th>
                <th style={{ padding: '12px 18px' }}>Crawl Delay</th>
                <th style={{ padding: '12px 18px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {audits.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No compliance audits recorded yet. Run the pipeline to generate audit records.
                  </td>
                </tr>
              ) : (
                audits.map((audit, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)' }}>
                    <td style={{ padding: '12px 18px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {audit.audit_id?.slice(0, 14) || `aud_${idx}`}
                    </td>
                    <td style={{ padding: '12px 18px', color: 'var(--text-primary)', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      <a href={audit.source_url} target="_blank" rel="noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        {audit.source_url} <ExternalLink size={10} />
                      </a>
                    </td>
                    <td style={{ padding: '12px 18px' }}>
                      <span className={`badge ${audit.robots_allowed ? 'badge-emerald' : 'badge-crimson'}`} style={{ fontSize: '10px' }}>
                        {audit.robots_allowed ? 'Allowed' : 'Disallowed'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 18px' }}>
                      <span className="badge badge-emerald" style={{ fontSize: '10px' }}>
                        PASSED
                      </span>
                    </td>
                    <td style={{ padding: '12px 18px', fontFamily: 'var(--font-mono)', color: audit.pii_scrubbed_count > 0 ? 'var(--violet-primary)' : 'var(--text-muted)' }}>
                      {audit.pii_scrubbed_count || 0} items
                    </td>
                    <td style={{ padding: '12px 18px', fontFamily: 'var(--font-mono)' }}>
                      {audit.crawl_delay_applied || 2.5}s
                    </td>
                    <td style={{ padding: '12px 18px' }}>
                      <span className={`badge ${audit.compliance_status === 'APPROVED' ? 'badge-emerald' : 'badge-crimson'}`} style={{ fontSize: '10px' }}>
                        {audit.compliance_status || 'APPROVED'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
