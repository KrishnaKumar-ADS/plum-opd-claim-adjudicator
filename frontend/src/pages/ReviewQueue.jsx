import { useState, useEffect } from 'react';
import { getReviewQueue, submitManualReview } from '../services/api';
import ReviewCard from '../components/ReviewCard';

export default function ReviewQueue() {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(null);
  const [reviewForm, setReviewForm] = useState({ decision: 'APPROVED', approved_amount: 0, notes: '' });
  const [error, setError] = useState('');

  useEffect(() => { load(); }, []);

  // Update approved amount dynamically when decision or active claim changes
  useEffect(() => {
    if (reviewing) {
      const item = queue.find(q => q.claim?.claim_id === reviewing);
      if (item) {
        const claimAmt = item.claim?.claim_amount || 0;
        if (reviewForm.decision === 'APPROVED') {
          setReviewForm(p => ({ ...p, approved_amount: claimAmt }));
          setError('');
        } else if (reviewForm.decision === 'REJECTED') {
          setReviewForm(p => ({ ...p, approved_amount: 0 }));
          setError('');
        } else if (reviewForm.decision === 'PARTIAL') {
          // Set to a reasonable default value (e.g. claimAmt - 1)
          if (reviewForm.approved_amount >= claimAmt || reviewForm.approved_amount <= 0) {
            setReviewForm(p => ({ ...p, approved_amount: Math.max(0, claimAmt - 1) }));
          }
        }
      }
    }
  }, [reviewForm.decision, reviewing]);

  const load = async () => {
    try {
      const res = await getReviewQueue();
      setQueue(res.data.queue || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleReview = async (claimId) => {
    setReviewing(claimId);
    setError('');
    const item = queue.find(q => q.claim?.claim_id === claimId);
    if (item) setReviewForm({ decision: 'APPROVED', approved_amount: item.claim?.claim_amount || 0, notes: '' });
  };

  const submitReview = async () => {
    const item = queue.find(q => q.claim?.claim_id === reviewing);
    const claimAmt = item?.claim?.claim_amount || 0;

    if (reviewForm.decision === 'APPROVED' && reviewForm.approved_amount !== claimAmt) {
      setError(`Approved amount must be exactly the original claim amount (₹${claimAmt})`);
      return;
    }
    if (reviewForm.decision === 'PARTIAL') {
      if (reviewForm.approved_amount >= claimAmt) {
        setError(`Partially approved amount must be strictly less than original claim amount (₹${claimAmt})`);
        return;
      }
      if (reviewForm.approved_amount <= 0) {
        setError('Partially approved amount must be greater than ₹0');
        return;
      }
    }

    try {
      await submitManualReview(reviewing, reviewForm);
      setReviewing(null);
      setError('');
      load();
    } catch (e) {
      console.error(e);
      setError(e.response?.data?.detail || 'Failed to submit review');
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Review Queue</h1>
        <p className="page-subtitle">Claims flagged for manual review or under appeal</p>
      </div>

      {reviewing && (
        <div className="card" style={{ marginBottom: 20, borderLeft: '4px solid var(--info)' }}>
          <div className="card-header"><h3 className="card-title">Review: {reviewing}</h3></div>
          
          {error && (
            <div className="alert alert-danger" style={{ marginBottom: 16 }}>
              {error}
            </div>
          )}

          <div className="grid-3">
            <div className="form-group">
              <label className="form-label">Decision</label>
              <select className="form-select" value={reviewForm.decision} onChange={e => setReviewForm(p => ({ ...p, decision: e.target.value }))}>
                <option value="APPROVED">Approve</option>
                <option value="REJECTED">Reject</option>
                <option value="PARTIAL">Partial</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Approved Amount (₹)</label>
              <input 
                className="form-input" 
                type="number" 
                value={reviewForm.approved_amount} 
                onChange={e => setReviewForm(p => ({ ...p, approved_amount: +e.target.value }))}
                disabled={reviewForm.decision === 'APPROVED' || reviewForm.decision === 'REJECTED'}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Notes</label>
              <input className="form-input" value={reviewForm.notes} onChange={e => setReviewForm(p => ({ ...p, notes: e.target.value }))} placeholder="Reviewer notes..." />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" onClick={submitReview}>Submit Review</button>
            <button className="btn btn-secondary" onClick={() => setReviewing(null)}>Cancel</button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="card"><div className="loading"><span className="spinner" /> Loading...</div></div>
      ) : queue.length === 0 ? (
        <div className="card"><div className="empty-state"><div className="empty-state-icon">✅</div><div className="empty-state-text">No claims pending review</div></div></div>
      ) : (
        queue.map((item, i) => (
          <ReviewCard 
            key={i} 
            claim={item.claim} 
            decision={item.decision} 
            type={item.type}
            appealReason={item.appeal_reason}
            appealSupportingInfo={item.appeal_supporting_info}
            onReview={handleReview} 
          />
        ))
      )}
    </div>
  );
}
