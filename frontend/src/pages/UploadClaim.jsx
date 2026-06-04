import { useState } from 'react';
import FileUploader from '../components/FileUploader';
import DecisionCard from '../components/DecisionCard';
import { submitClaim, submitClaimJSON } from '../services/api';

export default function UploadClaim() {
  const [mode, setMode] = useState('form'); // 'form' or 'json'
  const [form, setForm] = useState({
    member_id: '', member_name: '', treatment_date: '', claim_amount: '',
    hospital: '', cashless_request: false, member_join_date: '',
  });
  const [jsonInput, setJsonInput] = useState('');
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setLoadingStep(0); setError(''); setResult(null);
    const interval = setInterval(() => {
      setLoadingStep(s => (s < 3 ? s + 1 : s));
    }, 1200);

    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => { if (v !== '') fd.append(k, v); });
      files.forEach(f => fd.append('files', f));
      const res = await submitClaim(fd);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Submission failed');
    } finally {
      clearInterval(interval);
      setLoading(false);
    }
  };

  const handleJsonSubmit = async () => {
    setLoading(true); setLoadingStep(0); setError(''); setResult(null);
    const interval = setInterval(() => {
      setLoadingStep(s => (s < 3 ? s + 1 : s));
    }, 1200);

    try {
      const data = JSON.parse(jsonInput);
      const res = await submitClaimJSON(data);
      setResult(res.data);
    } catch (err) {
      setError(err.message || 'Invalid JSON or submission failed');
    } finally {
      clearInterval(interval);
      setLoading(false);
    }
  };

  const update = (k, v) => setForm(p => ({ ...p, [k]: v }));

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Submit Claim</h1>
        <p className="page-subtitle">Upload medical documents for automated adjudication</p>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        <button className={`btn ${mode === 'form' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setMode('form')}>📋 Form Upload</button>
        <button className={`btn ${mode === 'json' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setMode('json')}>🔧 JSON Input</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="grid-2">
        <div className="card">
          <div className="card-header"><h3 className="card-title">Claim Details</h3></div>

          {mode === 'form' ? (
            <form onSubmit={handleFormSubmit}>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Member ID *</label>
                  <input className="form-input" value={form.member_id} onChange={e => update('member_id', e.target.value)} placeholder="EMP001" required />
                </div>
                <div className="form-group">
                  <label className="form-label">Member Name *</label>
                  <input className="form-input" value={form.member_name} onChange={e => update('member_name', e.target.value)} placeholder="Full name" required />
                </div>
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Treatment Date *</label>
                  <input className="form-input" type="date" value={form.treatment_date} onChange={e => update('treatment_date', e.target.value)} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Claim Amount (₹) *</label>
                  <input className="form-input" type="number" value={form.claim_amount} onChange={e => update('claim_amount', e.target.value)} placeholder="1500" required />
                </div>
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Hospital</label>
                  <input className="form-input" value={form.hospital} onChange={e => update('hospital', e.target.value)} placeholder="Hospital name" />
                </div>
                <div className="form-group">
                  <label className="form-label">Join Date</label>
                  <input className="form-input" type="date" value={form.member_join_date} onChange={e => update('member_join_date', e.target.value)} />
                </div>
              </div>
              <div className="form-group">
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input type="checkbox" checked={form.cashless_request} onChange={e => update('cashless_request', e.target.checked)} />
                  <span className="form-label" style={{ margin: 0 }}>Cashless Request</span>
                </label>
              </div>
              <div className="form-group">
                <label className="form-label">Upload Documents</label>
                <FileUploader onFilesChange={setFiles} />
              </div>
              <button className="btn btn-primary" type="submit" disabled={loading}>
                {loading ? <><span className="spinner" style={{ width: 16, height: 16, marginRight: 8 }} /> Processing...</> : '🚀 Submit & Adjudicate'}
              </button>
            </form>
          ) : (
            <div>
              <div className="form-group">
                <label className="form-label">Claim JSON</label>
                <textarea className="form-textarea" style={{ minHeight: 300, fontFamily: 'monospace', fontSize: 12 }}
                  value={jsonInput} onChange={e => setJsonInput(e.target.value)}
                  placeholder='{"member_id": "EMP001", "member_name": "Rajesh Kumar", ...}'
                />
              </div>
              <button className="btn btn-primary" onClick={handleJsonSubmit} disabled={loading}>
                {loading ? 'Processing...' : '🚀 Submit JSON'}
              </button>
            </div>
          )}
        </div>

        <div>
          {loading && (
            <div className="card" style={{ borderLeft: '4px solid var(--info)' }}>
              <div className="card-header"><h3 className="card-title">Adjudication Pipeline</h3></div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                  <span className="badge badge-approved" style={{ padding: '2px 6px', fontSize: 10 }}>✓</span>
                  <span>1. Claim details submitted</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                  <span className={`badge ${loadingStep >= 1 ? 'badge-approved' : 'badge-manual'}`} style={{ padding: '2px 6px', fontSize: 10 }}>
                    {loadingStep > 1 ? '✓' : loadingStep === 1 ? '⚙' : '○'}
                  </span>
                  <span style={{ opacity: loadingStep >= 1 ? 1 : 0.5, fontWeight: loadingStep === 1 ? 600 : 400 }}>2. Running Vision OCR (Gemini 2.5 Flash)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                  <span className={`badge ${loadingStep >= 2 ? 'badge-approved' : 'badge-manual'}`} style={{ padding: '2px 6px', fontSize: 10 }}>
                    {loadingStep > 2 ? '✓' : loadingStep === 2 ? '⚙' : '○'}
                  </span>
                  <span style={{ opacity: loadingStep >= 2 ? 1 : 0.5, fontWeight: loadingStep === 2 ? 600 : 400 }}>3. Extracting metadata (Llama 3.3 70B)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                  <span className={`badge ${loadingStep >= 3 ? 'badge-approved' : 'badge-manual'}`} style={{ padding: '2px 6px', fontSize: 10 }}>
                    {loadingStep === 3 ? '⚙' : '○'}
                  </span>
                  <span style={{ opacity: loadingStep >= 3 ? 1 : 0.5, fontWeight: loadingStep === 3 ? 600 : 400 }}>4. Adjudicating policy, necessity (RAG) & fraud</span>
                </div>
              </div>
            </div>
          )}
          {result && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Adjudication Result</h3>
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{result.claim_id}</span>
              </div>
              <DecisionCard decision={result.decision} />
            </div>
          )}
          {!loading && !result && (
            <div className="card">
              <div className="empty-state">
                <div className="empty-state-icon">📋</div>
                <div className="empty-state-text">Submit a claim to see the adjudication result</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
