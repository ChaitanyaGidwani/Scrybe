import React, { useState, useMemo } from 'react';

export default function MatrixView({ records, onRefresh, searchQuery = '' }) {
  const [selectedCompany, setSelectedCompany] = useState('ALL');
  const [localSearch, setLocalSearch] = useState('');
  const [sortBy, setSortBy] = useState('input_asc');

  // Flatten all pricing tiers with company info
  const allRows = useMemo(() => {
    const rows = [];
    (records || []).forEach((rec) => {
      const company = rec.company_name || 'Unknown';
      const product = rec.product_name || 'AI Platform';
      const sourceUrl = rec.source_url || '';

      (rec.pricing_tiers || []).forEach((tier) => {
        rows.push({
          company,
          product,
          sourceUrl,
          modelName: tier.model_name || tier.tier_name || 'Standard Tier',
          inputPrice: tier.input_price_per_1m != null ? Number(tier.input_price_per_1m) : null,
          outputPrice: tier.output_price_per_1m != null ? Number(tier.output_price_per_1m) : null,
          cachePrice: tier.cache_price_per_1m != null ? Number(tier.cache_price_per_1m) : null,
          contextWindow: tier.context_window || null,
        });
      });
    });
    return rows;
  }, [records]);

  // List of unique companies for filter tabs
  const companies = useMemo(() => {
    const set = new Set();
    allRows.forEach((r) => set.add(r.company));
    return ['ALL', ...Array.from(set)];
  }, [allRows]);

  // Combined search term
  const activeSearch = (searchQuery || localSearch).trim().toLowerCase();

  // Filtered & sorted rows
  const filteredRows = useMemo(() => {
    let list = allRows;

    if (selectedCompany !== 'ALL') {
      list = list.filter((r) => r.company.toLowerCase() === selectedCompany.toLowerCase());
    }

    if (activeSearch) {
      list = list.filter(
        (r) =>
          r.company.toLowerCase().includes(activeSearch) ||
          r.modelName.toLowerCase().includes(activeSearch) ||
          r.product.toLowerCase().includes(activeSearch)
      );
    }

    // Sort
    return [...list].sort((a, b) => {
      if (sortBy === 'input_asc') {
        if (a.inputPrice == null) return 1;
        if (b.inputPrice == null) return -1;
        return a.inputPrice - b.inputPrice;
      }
      if (sortBy === 'input_desc') {
        if (a.inputPrice == null) return 1;
        if (b.inputPrice == null) return -1;
        return b.inputPrice - a.inputPrice;
      }
      if (sortBy === 'output_asc') {
        if (a.outputPrice == null) return 1;
        if (b.outputPrice == null) return -1;
        return a.outputPrice - b.outputPrice;
      }
      if (sortBy === 'name') {
        return a.modelName.localeCompare(b.modelName);
      }
      return 0;
    });
  }, [allRows, selectedCompany, activeSearch, sortBy]);

  // Export CSV
  const handleExportCSV = () => {
    if (filteredRows.length === 0) return;
    const headers = ['Company', 'Product', 'Model', 'Input Price ($/1M)', 'Output Price ($/1M)', 'Cache Price ($/1M)', 'Context Window'];
    const csvContent = [
      headers.join(','),
      ...filteredRows.map((r) =>
        [
          `"${r.company}"`,
          `"${r.product}"`,
          `"${r.modelName}"`,
          r.inputPrice != null ? r.inputPrice : '',
          r.outputPrice != null ? r.outputPrice : '',
          r.cachePrice != null ? r.cachePrice : '',
          r.contextWindow || '',
        ].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scrybe_pricing_matrix_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card">
      {/* ── Table Header Controls ── */}
      <div className="table-controls-bar">
        <div className="table-filters-left">
          {/* Company filter chips */}
          <div className="filter-chips">
            {companies.map((c) => (
              <button
                key={c}
                type="button"
                className={`filter-chip ${selectedCompany === c ? 'active' : ''}`}
                onClick={() => setSelectedCompany(c)}
              >
                {c === 'ALL' ? 'All Providers' : c}
              </button>
            ))}
          </div>
        </div>

        <div className="table-filters-right">
          {/* Search within table */}
          {!searchQuery && (
            <div className="search-bar table-search">
              <span className="material-symbols-outlined search-icon">search</span>
              <input
                type="text"
                placeholder="Filter models..."
                value={localSearch}
                onChange={(e) => setLocalSearch(e.target.value)}
              />
            </div>
          )}

          {/* Sort selector */}
          <select
            className="filter-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="input_asc">Sort: Lowest Input Price</option>
            <option value="input_desc">Sort: Highest Input Price</option>
            <option value="output_asc">Sort: Lowest Output Price</option>
            <option value="name">Sort: Model Name</option>
          </select>

          <button
            className="btn btn-secondary"
            onClick={handleExportCSV}
            title="Export filtered records as CSV"
            type="button"
          >
            <span className="material-symbols-outlined">download</span>
            <span>CSV</span>
          </button>

          <button
            className="btn btn-secondary btn-icon-only"
            onClick={onRefresh}
            title="Refresh pricing table"
            type="button"
          >
            <span className="material-symbols-outlined">refresh</span>
          </button>
        </div>
      </div>

      {/* ── Pricing Matrix Table ── */}
      {filteredRows.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '22%' }}>PROVIDER</th>
                <th style={{ width: '26%' }}>MODEL / TIER</th>
                <th style={{ width: '13%', textAlign: 'right' }}>INPUT / 1M</th>
                <th style={{ width: '13%', textAlign: 'right' }}>OUTPUT / 1M</th>
                <th style={{ width: '13%', textAlign: 'right' }}>CACHE / 1M</th>
                <th style={{ width: '13%', textAlign: 'right' }}>CONTEXT</th>
              </tr>
            </thead>
            <tbody>
              {filteredRows.map((row, i) => (
                <tr key={i}>
                  <td className="company-cell">
                    <span className="company-avatar">{row.company.charAt(0)}</span>
                    <div>
                      <div className="company-name">{row.company}</div>
                      <div className="company-product">{row.product}</div>
                    </div>
                  </td>
                  <td>
                    <div className="model-name-cell">
                      <span className="model-primary-name">{row.modelName}</span>
                    </div>
                  </td>
                  <td className="mono" style={{ textAlign: 'right' }}>
                    {row.inputPrice != null ? (
                      <span className="price-tag input-price">${row.inputPrice.toFixed(row.inputPrice < 0.01 ? 4 : 2)}</span>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  <td className="mono" style={{ textAlign: 'right' }}>
                    {row.outputPrice != null ? (
                      <span className="price-tag output-price">${row.outputPrice.toFixed(row.outputPrice < 0.01 ? 4 : 2)}</span>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  <td className="mono text-muted" style={{ textAlign: 'right' }}>
                    {row.cachePrice != null ? `$${row.cachePrice.toFixed(2)}` : '—'}
                  </td>
                  <td className="mono text-muted" style={{ textAlign: 'right' }}>
                    {row.contextWindow ? (
                      <span className="badge badge-purple">{`${(row.contextWindow / 1000).toFixed(0)}K`}</span>
                    ) : (
                      '—'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-icon">
            <span className="material-symbols-outlined">search_off</span>
          </div>
          <h4 className="empty-title">No matching pricing models found</h4>
          <p className="empty-desc">
            {allRows.length === 0
              ? 'Run a market scan to fetch current competitor rates.'
              : 'Try clearing your search query or provider filter.'}
          </p>
        </div>
      )}

      {/* Footer count indicator */}
      {filteredRows.length > 0 && (
        <div className="table-footer-bar">
          <span className="text-muted" style={{ fontSize: 13 }}>
            Showing <strong>{filteredRows.length}</strong> of <strong>{allRows.length}</strong> tracked model tiers
          </span>
          <span className="text-muted" style={{ fontSize: 12 }}>
            Normalized to standard USD ($) per 1 Million tokens
          </span>
        </div>
      )}
    </div>
  );
}
