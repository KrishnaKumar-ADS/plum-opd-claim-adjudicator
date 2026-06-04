import { useState, useEffect } from 'react';
import { getClaims, getClaim } from '../services/api';
import DecisionCard from '../components/DecisionCard';

const badgeClass = {
  APPROVED: 'badge-approved', REJECTED: 'badge-rejected',
  PARTIAL: 'badge-partial', MANUAL_REVIEW: 'badge-manual',
  SUBMITTED: 'badge-submitted', PROCESSING: 'badge-submitted',
  ADJUDICATED: 'badge-approved',
};

export default function ClaimStatus() {
  const [claims, setClaims] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadClaims(); }, []);

  const loadClaims = async () => {
    try {
      const res = await getClaims();
      setClaims(res.data.claims || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const viewClaim = async (id) => {
    try {
      const res = await getClaim(id);
      setSelected(res.data);
    } catch (e) { console.error(e); }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Claim Status</h1>
        <p className="page-subtitle">View and track your submitted claims</p>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">All Claims</h3>
            <button className="btn btn-secondary" onClick={loadClaims} style={{ padding: '6px 12px', fontSize: 12 }}>↻ Refresh</button>
          </div>

          {loading ? (
            <div className="loading"><span className="spinner" /> Loading claims...</div>
          ) : claims.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📭</div>
              <div className="empty-state-text">No claims submitted yet</div>
            </div>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr><th>Claim ID</th><th>Member</th><th>Amount</th><th>Status</th><th></th></tr>
                </thead>
                <tbody>
                  {claims.map(c => (
                    <tr key={c.claim_id} style={{ cursor: 'pointer' }} onClick={() => viewClaim(c.claim_id)}>
                      <td><strong>{c.claim_id}</strong></td>
                      <td>{c.member_name}</td>
                      <td>₹{c.claim_amount?.toLocaleString()}</td>
                      <td><span className={`badge ${badgeClass[c.status] || ''}`}>{c.status}</span></td>
                      <td><button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }}>View</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div>
          {selected ? (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">{selected.claim?.claim_id}</h3>
                <span className={`badge ${badgeClass[selected.claim?.status]}`}>{selected.claim?.status}</span>
              </div>

              <div style={{ marginBottom: 16, fontSize: 14 }}>
                <div style={{ display: 'flex', gap: 24, marginBottom: 8 }}>
                  <div><span style={{ color: 'var(--text-muted)' }}>Member:</span> {selected.claim?.member_name}</div>
                  <div><span style={{ color: 'var(--text-muted)' }}>ID:</span> {selected.claim?.member_id}</div>
                </div>
                <div style={{ display: 'flex', gap: 24 }}>
                  <div><span style={{ color: 'var(--text-muted)' }}>Treatment:</span> {selected.claim?.treatment_date}</div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Amount:</span> ₹{selected.claim?.claim_amount?.toLocaleString()}</div>
                </div>
              </div>

              {selected.decision && (
                <>
                  <h4 style={{ marginBottom: 12, fontSize: 14, color: 'var(--text-secondary)' }}>DECISION</h4>
                  <DecisionCard decision={selected.decision} />
                </>
              )}
            </div>
          ) : (
            <div className="card">
              <div className="empty-state">
                <div className="empty-state-icon">👈</div>
                <div className="empty-state-text">Select a claim to view details</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
