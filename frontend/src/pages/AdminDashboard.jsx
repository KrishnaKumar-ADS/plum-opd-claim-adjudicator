import { useState, useEffect } from 'react';
import { getStats, runEvaluation, getEvalResults } from '../services/api';
import MetricsCard from '../components/MetricsCard';
import ConfidenceMeter from '../components/ConfidenceMeter';

const TAB_OVERVIEW = 'overview';
const TAB_EVAL = 'evaluation';

export default function AdminDashboard() {
  const [tab, setTab] = useState(TAB_OVERVIEW);
  const [stats, setStats] = useState(null);
  const [evalResults, setEvalResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [evalLoading, setEvalLoading] = useState(false);

  useEffect(() => {
    loadStats();
    // Try to load cached eval results
    getEvalResults().then(r => setEvalResults(r.data)).catch(() => {});
  }, []);

  const loadStats = async () => {
    try {
      const res = await getStats();
      setStats(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleRunEval = async () => {
    setEvalLoading(true);
    try {
      const res = await runEvaluation();
      setEvalResults(res.data);
    } catch (e) { console.error(e); }
    finally { setEvalLoading(false); }
  };

  if (loading) return <div className="loading"><span className="spinner" /> Loading dashboard...</div>;

  const d = stats?.decisions || {};
  const f = stats?.financials || {};
  const p = stats?.performance || {};

  const totalDecisions = (d.approved || 0) + (d.rejected || 0) + (d.partial || 0) + (d.manual_review || 0);
  const approvalRate = totalDecisions > 0 ? ((d.approved || 0) / totalDecisions * 100).toFixed(1) : '0.0';

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Admin Dashboard</h1>
        <p className="page-subtitle">System overview, performance metrics & evaluation suite</p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid var(--border)', paddingBottom: 0 }}>
        {[
          { id: TAB_OVERVIEW, label: '📊 Overview' },
          { id: TAB_EVAL, label: '🧪 Evaluation Suite' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              padding: '10px 20px',
              border: 'none',
              borderBottom: tab === t.id ? '2px solid var(--accent)' : '2px solid transparent',
              background: 'none',
              cursor: 'pointer',
              fontWeight: tab === t.id ? 600 : 400,
              color: tab === t.id ? 'var(--accent)' : 'var(--text-secondary)',
              fontSize: 14,
              transition: 'all 0.2s',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW TAB ── */}
      {tab === TAB_OVERVIEW && (
        <>
          <div className="stats-grid">
            <MetricsCard title="Total Claims" value={stats?.total_claims || 0} icon="📋" />
            <MetricsCard title="Approved" value={d.approved || 0} color="var(--success)" icon="✅" />
            <MetricsCard title="Rejected" value={d.rejected || 0} color="var(--danger)" icon="❌" />
            <MetricsCard title="Partial" value={d.partial || 0} color="var(--warning)" icon="⚠️" />
            <MetricsCard title="Manual Review" value={d.manual_review || 0} color="var(--info)" icon="👁️" />
            <MetricsCard title="Pending Appeals" value={stats?.pending_appeals || 0} icon="📝" />
          </div>

          <div className="grid-2" style={{ marginBottom: 20 }}>
            <div className="card">
              <div className="card-header"><h3 className="card-title">💰 Financials</h3></div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {[
                  { label: 'Total Claimed', value: `₹${(f.total_claimed || 0).toLocaleString()}`, color: 'var(--text-primary)' },
                  { label: 'Total Approved', value: `₹${(f.total_approved || 0).toLocaleString()}`, color: 'var(--success)' },
                  { label: 'Savings / Reductions', value: `₹${(f.savings || 0).toLocaleString()}`, color: 'var(--accent)' },
                ].map(row => (
                  <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border-light)' }}>
                    <span style={{ fontSize: 13, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{row.label}</span>
                    <span style={{ fontSize: 20, fontWeight: 700, color: row.color }}>{row.value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="card-header"><h3 className="card-title">⚡ Performance</h3></div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>Avg Confidence Score</div>
                  <ConfidenceMeter score={p.avg_confidence || 0} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-light)' }}>
                  <span style={{ fontSize: 13, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Avg Processing Time</span>
                  <span style={{ fontSize: 18, fontWeight: 700 }}>{(p.avg_processing_ms || 0).toFixed(0)}ms</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
                  <span style={{ fontSize: 13, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Approval Rate</span>
                  <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--success)' }}>{approvalRate}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Decision Breakdown Bar */}
          {totalDecisions > 0 && (
            <div className="card">
              <div className="card-header"><h3 className="card-title">📈 Decision Breakdown</h3></div>
              <div style={{ display: 'flex', gap: 2, height: 32, borderRadius: 6, overflow: 'hidden', marginBottom: 12 }}>
                {[
                  { count: d.approved || 0, color: 'var(--success)', label: 'Approved' },
                  { count: d.partial || 0, color: 'var(--warning)', label: 'Partial' },
                  { count: d.manual_review || 0, color: 'var(--info)', label: 'Manual' },
                  { count: d.rejected || 0, color: 'var(--danger)', label: 'Rejected' },
                ].filter(seg => seg.count > 0).map(seg => (
                  <div
                    key={seg.label}
                    title={`${seg.label}: ${seg.count}`}
                    style={{
                      flex: seg.count,
                      background: seg.color,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontSize: 11,
                      fontWeight: 600,
                    }}
                  >
                    {seg.count > 1 ? seg.count : ''}
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                {[
                  { label: 'Approved', count: d.approved || 0, color: 'var(--success)' },
                  { label: 'Partial', count: d.partial || 0, color: 'var(--warning)' },
                  { label: 'Manual Review', count: d.manual_review || 0, color: 'var(--info)' },
                  { label: 'Rejected', count: d.rejected || 0, color: 'var(--danger)' },
                ].map(seg => (
                  <div key={seg.label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                    <span style={{ width: 10, height: 10, borderRadius: 2, background: seg.color, display: 'inline-block' }} />
                    <span style={{ color: 'var(--text-muted)' }}>{seg.label}:</span>
                    <strong>{seg.count}</strong>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* ── EVALUATION TAB ── */}
      {tab === TAB_EVAL && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🧪 AI Evaluation Suite</h3>
            <button
              className="btn btn-primary"
              onClick={handleRunEval}
              disabled={evalLoading}
              style={{ padding: '8px 16px', fontSize: 13 }}
            >
              {evalLoading ? <><span className="spinner" style={{ width: 14, height: 14, marginRight: 6 }} />Running...</> : '▶ Run Tests'}
            </button>
          </div>

          {evalResults ? (
            <div>
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 20 }}>
                <div style={{ background: 'var(--accent-light)', padding: '12px 20px', borderRadius: 8, textAlign: 'center', minWidth: 120 }}>
                  <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--accent)' }}>{(evalResults.accuracy * 100).toFixed(1)}%</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>ACCURACY</div>
                </div>
                <div style={{ background: 'var(--success-light)', padding: '12px 20px', borderRadius: 8, textAlign: 'center', minWidth: 120 }}>
                  <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--success)' }}>{evalResults.correct}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>CORRECT</div>
                </div>
                <div style={{ background: 'var(--danger-light)', padding: '12px 20px', borderRadius: 8, textAlign: 'center', minWidth: 120 }}>
                  <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--danger)' }}>{evalResults.total - evalResults.correct}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>INCORRECT</div>
                </div>
                <div style={{ background: 'var(--bg-secondary)', padding: '12px 20px', borderRadius: 8, textAlign: 'center', minWidth: 120 }}>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>{evalResults.total}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>TOTAL CASES</div>
                </div>
              </div>

              {/* Accuracy progress bar */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12, color: 'var(--text-muted)' }}>
                  <span>Test Pass Rate</span>
                  <span>{evalResults.correct}/{evalResults.total}</span>
                </div>
                <div style={{ height: 8, background: 'var(--border-light)', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${evalResults.accuracy * 100}%`, background: evalResults.accuracy >= 0.8 ? 'var(--success)' : evalResults.accuracy >= 0.6 ? 'var(--warning)' : 'var(--danger)', borderRadius: 4, transition: 'width 0.5s ease' }} />
                </div>
              </div>

              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Case ID</th>
                      <th>Test Name</th>
                      <th>Expected</th>
                      <th>Actual</th>
                      <th>Confidence</th>
                      <th>Time</th>
                      <th>Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evalResults.results?.map(r => (
                      <tr key={r.case_id}>
                        <td><strong>{r.case_id}</strong></td>
                        <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.case_name}</td>
                        <td><span className="badge badge-submitted">{r.expected_decision}</span></td>
                        <td><span className={`badge ${r.correct ? 'badge-approved' : 'badge-rejected'}`}>{r.actual_decision || '—'}</span></td>
                        <td style={{ minWidth: 120 }}>
                          {r.confidence != null ? <ConfidenceMeter score={r.confidence} /> : '—'}
                        </td>
                        <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{r.processing_time_ms ? `${r.processing_time_ms}ms` : '—'}</td>
                        <td style={{ fontSize: 18 }}>{r.error ? '💥' : r.correct ? '✅' : '❌'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="empty-state" style={{ padding: 40 }}>
              <div className="empty-state-icon">🧪</div>
              <div className="empty-state-text">Click "Run Tests" to evaluate AI accuracy against test cases</div>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 8 }}>This runs adjudication on all test cases and compares against expected decisions</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
