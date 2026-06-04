import { useState, useEffect } from 'react';
import { getAppeals, getClaims } from '../services/api';
import AppealForm from '../components/AppealForm';

const badgeClass = {
  SUBMITTED: 'badge-submitted', UNDER_REVIEW: 'badge-manual',
  APPROVED: 'badge-approved', REJECTED: 'badge-rejected',
};

export default function Appeals() {
  const [appeals, setAppeals] = useState([]);
  const [claims, setClaims] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [selectedClaim, setSelectedClaim] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      const [aRes, cRes] = await Promise.all([getAppeals(), getClaims()]);
      setAppeals(aRes.data.appeals || []);
      setClaims(cRes.data.claims || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div>
          <h1 className="page-title">Appeals</h1>
          <p className="page-subtitle">Appeal rejected or partial decisions</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Cancel' : '+ New Appeal'}
        </button>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header"><h3 className="card-title">File an Appeal</h3></div>
          <div className="form-group">
            <label className="form-label">Select Claim</label>
            <select className="form-select" value={selectedClaim} onChange={e => setSelectedClaim(e.target.value)}>
              <option value="">Choose a claim...</option>
              {claims.filter(c => c.status === 'ADJUDICATED').map(c => (
                <option key={c.claim_id} value={c.claim_id}>{c.claim_id} - {c.member_name} - ₹{c.claim_amount}</option>
              ))}
            </select>
          </div>
          {selectedClaim && <AppealForm claimId={selectedClaim} onSubmitted={() => { setShowForm(false); load(); }} />}
        </div>
      )}

      <div className="card">
        <div className="card-header"><h3 className="card-title">All Appeals</h3></div>
        {loading ? (
          <div className="loading"><span className="spinner" /> Loading...</div>
        ) : appeals.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📝</div>
            <div className="empty-state-text">No appeals filed yet</div>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr><th>Appeal ID</th><th>Claim ID</th><th>Reason</th><th>Status</th><th>Date</th></tr>
              </thead>
              <tbody>
                {appeals.map(a => (
                  <tr key={a.appeal_id}>
                    <td><strong>{a.appeal_id}</strong></td>
                    <td>{a.claim_id}</td>
                    <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.reason}</td>
                    <td><span className={`badge ${badgeClass[a.status]}`}>{a.status}</span></td>
                    <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{a.created_at?.slice(0, 10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
