import { useState, useEffect } from 'react';
import { getStats, runEvaluation, getEvalResults, getPolicyTerms } from '../services/api';
import MetricsCard from '../components/MetricsCard';
import ConfidenceMeter from '../components/ConfidenceMeter';

const TAB_OVERVIEW = 'overview';
const TAB_EVAL = 'evaluation';
const TAB_POLICY_TERMS = 'policy-terms';

export default function AdminDashboard() {
  const [tab, setTab] = useState(TAB_OVERVIEW);
  const [stats, setStats] = useState(null);
  const [evalResults, setEvalResults] = useState(null);
  const [policyTerms, setPolicyTerms] = useState(null);
  const [loading, setLoading] = useState(true);
  const [evalLoading, setEvalLoading] = useState(false);
  const [policyTermsLoading, setPolicyTermsLoading] = useState(false);

  useEffect(() => {
    loadStats();
    // Try to load cached eval results
    getEvalResults().then(r => setEvalResults(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (tab === TAB_POLICY_TERMS && !policyTerms) {
      loadPolicyTerms();
    }
  }, [tab]);

  const loadStats = async () => {
    try {
      const res = await getStats();
      setStats(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const loadPolicyTerms = async () => {
    setPolicyTermsLoading(true);
    try {
      const res = await getPolicyTerms();
      setPolicyTerms(res.data);
    } catch (e) {
      console.error("Failed to load policy terms:", e);
    } finally {
      setPolicyTermsLoading(false);
    }
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
          { id: TAB_POLICY_TERMS, label: '📜 Policy Terms' },
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

      {/* ── POLICY TERMS TAB ── */}
      {tab === TAB_POLICY_TERMS && (
        <div>
          {policyTermsLoading || !policyTerms ? (
            <div className="card"><div className="loading"><span className="spinner" /> Loading policy terms...</div></div>
          ) : (
            <div>
              {/* Header Card */}
              <div className="card" style={{ marginBottom: 20, background: 'linear-gradient(135deg, var(--accent-light) 0%, rgba(255,255,255,0) 100%)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
                  <div>
                    <span className="badge badge-submitted" style={{ marginBottom: 8, display: 'inline-block' }}>{policyTerms.policy_id}</span>
                    <h2 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>{policyTerms.policy_name}</h2>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: '4px 0 0 0' }}>Effective Date: {policyTerms.effective_date}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Corporate Holder</div>
                    <strong>{policyTerms.policy_holder?.company}</strong>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>Employees Covered: {policyTerms.policy_holder?.employees_covered}</div>
                  </div>
                </div>
              </div>

              {/* Coverage Cards Grid */}
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, borderBottom: '1px solid var(--border-light)', paddingBottom: 8 }}>💼 Category Coverages & Sub-limits</h3>
              <div className="stats-grid" style={{ marginBottom: 24 }}>
                {Object.entries(policyTerms.coverage_details || {}).map(([key, val]) => {
                  if (typeof val !== 'object' || key === 'annual_limit' || key === 'per_claim_limit' || key === 'family_floater_limit') return null;
                  
                  // Label formatting
                  const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                  return (
                    <div className="card" key={key} style={{ padding: 16, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: 140 }}>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                          <strong style={{ fontSize: 14 }}>{label}</strong>
                          <span className={`badge ${val.covered ? 'badge-approved' : 'badge-rejected'}`} style={{ fontSize: 10 }}>
                            {val.covered ? 'COVERED' : 'EXCLUDED'}
                          </span>
                        </div>
                        {val.sub_limit && (
                          <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
                            ₹{val.sub_limit.toLocaleString()} <span style={{ fontSize: 11, fontWeight: 400, color: 'var(--text-muted)' }}>limit</span>
                          </div>
                        )}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8, borderTop: '1px solid var(--border-light)', paddingTop: 6 }}>
                        {val.copay_percentage != null && `Co-pay: ${val.copay_percentage}% | `}
                        {val.network_discount != null && `Discount: ${val.network_discount}% | `}
                        {val.generic_drugs_mandatory && `Generic Mandatory | `}
                        {val.covered_tests && `${val.covered_tests.length} tests listed | `}
                        {val.procedures_covered && `${val.procedures_covered.length} procedures | `}
                        {val.therapy_sessions_limit && `Max ${val.therapy_sessions_limit} sessions`}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Flex Columns */}
              <div className="grid-2" style={{ marginBottom: 20 }}>
                {/* Waiting Periods */}
                <div className="card">
                  <div className="card-header"><h3 className="card-title">⏳ Waiting Periods</h3></div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid var(--border-light)' }}>
                      <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Initial Waiting Period</span>
                      <strong>{policyTerms.waiting_periods?.initial_waiting} Days</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid var(--border-light)' }}>
                      <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Pre-Existing Diseases (PED)</span>
                      <strong>{policyTerms.waiting_periods?.pre_existing_diseases} Days</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid var(--border-light)' }}>
                      <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Maternity Waiting</span>
                      <strong>{policyTerms.waiting_periods?.maternity} Days</strong>
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>Ailment Specific Waiting:</div>
                      {Object.entries(policyTerms.waiting_periods?.specific_ailments || {}).map(([disease, days]) => (
                        <div key={disease} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0' }}>
                          <span style={{ textTransform: 'capitalize', color: 'var(--text-muted)' }}>{disease.replace(/_/g, ' ')}</span>
                          <strong>{days} Days</strong>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Exclusions */}
                <div className="card">
                  <div className="card-header"><h3 className="card-title">🚫 Exclusions (Not Covered)</h3></div>
                  <ul style={{ margin: 0, paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13, color: 'var(--text-secondary)' }}>
                    {policyTerms.exclusions?.map((ex, i) => (
                      <li key={i}>{ex}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="grid-2">
                {/* Network Hospitals */}
                <div className="card">
                  <div className="card-header"><h3 className="card-title">🏥 Network Hospitals</h3></div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {policyTerms.network_hospitals?.map((hosp, i) => (
                      <span key={i} className="badge badge-submitted" style={{ padding: '6px 12px', fontSize: 12, borderRadius: 4 }}>
                        🏥 {hosp}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Cashless Facilities */}
                <div className="card">
                  <div className="card-header"><h3 className="card-title">💳 Cashless & Claims</h3></div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                      <span style={{ color: 'var(--text-muted)' }}>Cashless Available</span>
                      <strong style={{ color: policyTerms.cashless_facilities?.available ? 'var(--success)' : 'var(--danger)' }}>
                        {policyTerms.cashless_facilities?.available ? 'YES' : 'NO'}
                      </strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                      <span style={{ color: 'var(--text-muted)' }}>Network Restricted Only</span>
                      <strong>{policyTerms.cashless_facilities?.network_only ? 'YES' : 'NO'}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                      <span style={{ color: 'var(--text-muted)' }}>Instant Approval Limit</span>
                      <strong>₹{policyTerms.cashless_facilities?.instant_approval_limit?.toLocaleString()}</strong>
                    </div>
                    <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 10, marginTop: 4 }}>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>Claim Timeline Guidelines:</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                        <span>Submission Deadline</span>
                        <strong>{policyTerms.claim_requirements?.submission_timeline_days} Days</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginTop: 4 }}>
                        <span>Min Claim Amount</span>
                        <strong>₹{policyTerms.claim_requirements?.minimum_claim_amount}</strong>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
