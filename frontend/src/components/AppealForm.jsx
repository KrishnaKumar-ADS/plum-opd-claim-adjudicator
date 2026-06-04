import { useState } from 'react';
import { createAppeal } from '../services/api';

export default function AppealForm({ claimId, onSubmitted }) {
  const [reason, setReason] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reason.trim()) return;
    setLoading(true);
    setError('');
    try {
      await createAppeal({ claim_id: claimId, reason, supporting_info: info });
      onSubmitted?.();
      setReason('');
      setInfo('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit appeal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="form-group">
        <label className="form-label">Reason for Appeal *</label>
        <textarea className="form-textarea" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Explain why you disagree with the decision..." required />
      </div>
      <div className="form-group">
        <label className="form-label">Supporting Information</label>
        <textarea className="form-textarea" value={info} onChange={(e) => setInfo(e.target.value)} placeholder="Any additional details or evidence..." />
      </div>
      <button className="btn btn-primary" type="submit" disabled={loading}>
        {loading ? 'Submitting...' : 'Submit Appeal'}
      </button>
    </form>
  );
}
