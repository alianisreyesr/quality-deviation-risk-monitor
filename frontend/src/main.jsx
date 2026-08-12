import { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api';
const RISK_LEVELS = ['All', 'High', 'Medium', 'Low'];

function RiskBadge({ level }) {
  return <span className={`risk-badge risk-${level.toLowerCase()}`}>{level}</span>;
}

function StatCard({ label, value, tone, onClick, selected }) {
  return (
    <button className={`stat-card ${tone} ${selected ? 'selected' : ''}`} onClick={onClick}>
      <span>{label}</span>
      <strong>{value}</strong>
    </button>
  );
}

function DeviationTable({ records, onSelect }) {
  if (!records.length) {
    return <div className="empty-state">No deviations match the selected filters.</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Deviation</th><th>Severity</th><th>Due date</th><th>Owner</th><th>Risk signal</th><th /></tr></thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.deviation_id}>
              <td><strong>{record.deviation_id}</strong><span>{record.title}</span></td>
              <td>{record.severity}</td>
              <td>{record.due_date}</td>
              <td>{record.investigation_owner || 'Unassigned'}</td>
              <td><RiskBadge level={record.risk_level} /><span className="score">{record.risk_score} points</span></td>
              <td><button className="review-button" onClick={() => onSelect(record)}>Review</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ReviewPanel({ record, onClose }) {
  if (!record) return null;
  return (
    <div className="panel-backdrop" onClick={onClose}>
      <aside className="review-panel" onClick={(event) => event.stopPropagation()}>
        <button className="close-button" onClick={onClose} aria-label="Close review panel">×</button>
        <p className="eyebrow">EXPLAINABLE RISK REVIEW</p>
        <h2>{record.deviation_id}</h2>
        <p className="panel-title">{record.title}</p>
        <div className="panel-meta"><RiskBadge level={record.risk_level} /><span>{record.risk_score} total points</span></div>
        <h3>Why this record was flagged</h3>
        <ul>{record.risk_reasons.length ? record.risk_reasons.map((reason) => <li key={reason}>{reason}</li>) : <li>No active risk signals.</li>}</ul>
        <div className="review-note"><strong>Reviewer accountability</strong><br />This prioritization is advisory. A qualified reviewer must assess the record before making a quality decision.</div>
      </aside>
    </div>
  );
}

function App() {
  const [records, setRecords] = useState([]);
  const [summary, setSummary] = useState(null);
  const [riskFilter, setRiskFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([fetch(`${API_BASE_URL}/deviations`), fetch(`${API_BASE_URL}/summary`)])
      .then(async ([deviationsResponse, summaryResponse]) => {
        if (!deviationsResponse.ok || !summaryResponse.ok) throw new Error('API unavailable');
        const deviations = await deviationsResponse.json();
        setRecords(deviations.records);
        setSummary(await summaryResponse.json());
      })
      .catch(() => setError('Unable to load synthetic data. Start the FastAPI service on port 8000.'));
  }, []);

  const filteredRecords = useMemo(() => records.filter((record) => {
    const matchesRisk = riskFilter === 'All' || record.risk_level === riskFilter;
    const query = search.trim().toLowerCase();
    const matchesSearch = !query || `${record.deviation_id} ${record.title} ${record.investigation_owner || ''}`.toLowerCase().includes(query);
    return matchesRisk && matchesSearch;
  }), [records, riskFilter, search]);

  return (
    <main className="app-shell">
      <header>
        <div><p className="eyebrow">QUALITY SYSTEMS · PORTFOLIO PROTOTYPE</p><h1>Deviation Risk Monitor</h1><p className="subtitle">Transparent prioritization for synthetic quality-deviation records.</p></div>
        <div className="synthetic-notice">Synthetic data only<br />Human review required</div>
      </header>
      {error ? <div className="error">{error}</div> : <>
        <section className="metrics">
          {RISK_LEVELS.slice(1).map((level) => <StatCard key={level} label={`${level} risk`} value={summary?.risk_counts?.[level] ?? '—'} tone={level.toLowerCase()} selected={riskFilter === level} onClick={() => setRiskFilter(level)} />)}
          <StatCard label="Past due" value={summary?.overdue_records ?? '—'} tone="neutral" selected={riskFilter === 'All'} onClick={() => setRiskFilter('All')} />
        </section>
        <section className="workspace">
          <div className="toolbar"><div><h2>Reviewer queue</h2><p>{filteredRecords.length} records shown</p></div><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search ID, title, or owner" aria-label="Search deviations" /></div>
          <DeviationTable records={filteredRecords} onSelect={setSelectedRecord} />
        </section>
      </>}
      <footer>Risk scores are explainable rule-based signals, not predictive models or regulated quality decisions.</footer>
      <ReviewPanel record={selectedRecord} onClose={() => setSelectedRecord(null)} />
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
