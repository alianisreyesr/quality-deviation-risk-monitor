import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE = 'http://127.0.0.1:8000';

// --- Risk badge component ---
function RiskBadge({ level }) {
  return (
    <span className={`risk-badge risk-badge--${level.toLowerCase()}`}>
      {level}
    </span>
  );
}

// --- Summary cards at the top ---
function SummaryCards({ records, activeFilter, onFilterChange }) {
  const levels = ['High', 'Medium', 'Low'];
  return (
    <section className="summary-cards">
      {levels.map((level) => (
        <button
          key={level}
          className={`card card--${level.toLowerCase()} ${
            activeFilter === level ? 'card--active' : ''
          }`}
          onClick={() => onFilterChange(activeFilter === level ? 'All' : level)}
        >
          <span className="card__label">{level} Risk</span>
          <span className="card__count">
            {records.filter((r) => r.risk_level === level).length}
          </span>
        </button>
      ))}
      <button
        className={`card card--all ${activeFilter === 'All' ? 'card--active' : ''}`}
        onClick={() => onFilterChange('All')}
      >
        <span className="card__label">All</span>
        <span className="card__count">{records.length}</span>
      </button>
    </section>
  );
}

// --- Detail side panel for a single deviation ---
function DetailPanel({ deviation, onClose }) {
  if (!deviation) return null;
  return (
    <aside className="detail-panel">
      <button className="detail-panel__close" onClick={onClose}>
        &times; Close
      </button>
      <h2>{deviation.deviation_id}</h2>
      <p className="detail-panel__title">{deviation.title}</p>

      <dl className="detail-panel__meta">
        <dt>Severity</dt>
        <dd>{deviation.severity}</dd>
        <dt>Due Date</dt>
        <dd>{deviation.due_date}</dd>
        <dt>Owner</dt>
        <dd>{deviation.investigation_owner || 'Unassigned'}</dd>
        <dt>Review Status</dt>
        <dd>{deviation.review_status}</dd>
        <dt>Risk Score</dt>
        <dd>{deviation.risk_score}</dd>
      </dl>

      <h3>Why it was flagged</h3>
      <ul className="reason-list">
        {deviation.risk_reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>

      <p className="detail-panel__notice">
        Human review remains required. This score is advisory only.
      </p>
    </aside>
  );
}

// --- Deviations table ---
function DeviationTable({ records, onSelectDeviation }) {
  if (records.length === 0) {
    return <p className="empty-state">No records match the selected filter.</p>;
  }
  return (
    <table className="deviation-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Title</th>
          <th>Severity</th>
          <th>Due Date</th>
          <th>Owner</th>
          <th>Risk</th>
          <th>Status</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {records.map((record) => (
          <tr key={record.deviation_id}>
            <td>{record.deviation_id}</td>
            <td>{record.title}</td>
            <td>{record.severity}</td>
            <td>{record.due_date}</td>
            <td>{record.investigation_owner || <em>Unassigned</em>}</td>
            <td>
              <RiskBadge level={record.risk_level} />
              <span className="risk-score"> {record.risk_score}</span>
            </td>
            <td>{record.review_status}</td>
            <td>
              <button
                className="btn-review"
                onClick={() => onSelectDeviation(record)}
              >
                Review
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// --- Root app ---
function App() {
  const [allRecords, setAllRecords] = useState([]);
  const [activeFilter, setActiveFilter] = useState('All');
  const [selectedDeviation, setSelectedDeviation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/deviations`)
      .then((res) => {
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setAllRecords(data.records);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const filteredRecords =
    activeFilter === 'All'
      ? allRecords
      : allRecords.filter((r) => r.risk_level === activeFilter);

  return (
    <main>
      <header className="app-header">
        <p className="eyebrow">QUALITY DEVIATION RISK MONITOR</p>
        <h1>Reviewer Dashboard</h1>
        <p className="notice">
          Synthetic portfolio data — not for production or regulated
          decision-making.
        </p>
      </header>

      {loading && <p className="loading">Loading records…</p>}
      {error && <p className="error">Could not load data: {error}</p>}

      {!loading && !error && (
        <>
          <SummaryCards
            records={allRecords}
            activeFilter={activeFilter}
            onFilterChange={setActiveFilter}
          />
          <DeviationTable
            records={filteredRecords}
            onSelectDeviation={setSelectedDeviation}
          />
          <DetailPanel
            deviation={selectedDeviation}
            onClose={() => setSelectedDeviation(null)}
          />
        </>
      )}
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
