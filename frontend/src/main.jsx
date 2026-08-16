import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE = 'http://127.0.0.1:8000';

function App() {
  const [records, setRecords] = useState([]);
  const [filter, setFilter] = useState('All');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/deviations`)
      .then((res) => res.json())
      .then((data) => setRecords(data.records))
      .catch((err) => console.error('Failed to load deviations:', err));
  }, []);

  const filtered =
    filter === 'All'
      ? records
      : records.filter((r) => r.risk_level === filter);

  return (
    <main>
      <p className="eyebrow">QUALITY DEVIATION RISK MONITOR</p>
      <h1>Reviewer Dashboard</h1>
      <p className="notice">
        Synthetic portfolio data — not for production or regulated decision-making.
      </p>

      <section className="cards">
        {['High', 'Medium', 'Low'].map((level) => (
          <button
            key={level}
            className={level.toLowerCase()}
            onClick={() => setFilter(level)}
          >
            {level}
            <b>{records.filter((r) => r.risk_level === level).length}</b>
          </button>
        ))}
        <button onClick={() => setFilter('All')}>Show all</button>
      </section>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Deviation</th>
            <th>Risk</th>
            <th>Owner</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((record) => (
            <tr key={record.deviation_id}>
              <td>{record.deviation_id}</td>
              <td>{record.title}</td>
              <td>
                {record.risk_level} · {record.risk_score}
              </td>
              <td>{record.investigation_owner || 'Unassigned'}</td>
              <td>
                <button onClick={() => setSelected(record)}>Review reasons</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {selected && (
        <aside>
          <button onClick={() => setSelected(null)}>Close</button>
          <h2>{selected.deviation_id}</h2>
          <h3>Why it was flagged</h3>
          <ul>
            {selected.risk_reasons.map((reason, idx) => (
              <li key={idx}>{reason}</li>
            ))}
          </ul>
          <p>Human review remains required.</p>
        </aside>
      )}
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
