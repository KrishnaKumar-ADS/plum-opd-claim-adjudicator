import ConfidenceMeter from './ConfidenceMeter';

const badgeClass = {
  APPROVED: 'badge-approved', REJECTED: 'badge-rejected',
  PARTIAL: 'badge-partial', MANUAL_REVIEW: 'badge-manual',
};

export default function DecisionCard({ decision }) {
  if (!decision) return null;
  const d = decision;

  return (
    <div className={`decision-card ${d.decision?.toLowerCase()}`}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <span className={`badge ${badgeClass[d.decision] || ''}`}>{d.decision}</span>
        <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          {d.processing_time_ms}ms
        </span>
      </div>

      <div className="grid-2" style={{ gap: 12, marginBottom: 16 }}>
        <div className="decision-detail">
          <div className="decision-detail-label">Claimed Amount</div>
          <div className="decision-detail-value" style={{ fontSize: 18, fontWeight: 600 }}>
            ₹{d.claimed_amount?.toLocaleString()}
          </div>
        </div>
        <div className="decision-detail">
          <div className="decision-detail-label">Approved Amount</div>
          <div className="decision-detail-value" style={{ fontSize: 18, fontWeight: 600, color: d.approved_amount > 0 ? 'var(--success)' : 'var(--danger)' }}>
            ₹{d.approved_amount?.toLocaleString()}
          </div>
        </div>
      </div>

      <div className="decision-detail" style={{ marginBottom: 12 }}>
        <div className="decision-detail-label">Confidence</div>
        <ConfidenceMeter score={d.confidence_score} />
      </div>

      {d.rejection_reasons?.length > 0 && (
        <div className="decision-detail" style={{ marginBottom: 12 }}>
          <div className="decision-detail-label">Rejection Reasons</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
            {d.rejection_reasons.map((r, i) => (
              <span key={i} className="badge badge-rejected" style={{ fontSize: 11 }}>{r}</span>
            ))}
          </div>
        </div>
      )}

      {d.notes && (
        <div className="decision-detail" style={{ marginBottom: 12 }}>
          <div className="decision-detail-label">Notes</div>
          <div className="decision-detail-value">{d.notes}</div>
        </div>
      )}

      {d.next_steps && (
        <div className="decision-detail">
          <div className="decision-detail-label">Next Steps</div>
          <div className="decision-detail-value">{d.next_steps}</div>
        </div>
      )}
    </div>
  );
}
