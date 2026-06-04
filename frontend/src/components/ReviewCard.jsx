import ConfidenceMeter from './ConfidenceMeter';

const badgeClass = {
  APPROVED: 'badge-approved', REJECTED: 'badge-rejected',
  PARTIAL: 'badge-partial', MANUAL_REVIEW: 'badge-manual',
};

export default function ReviewCard({ claim, decision, type, appealReason, appealSupportingInfo, onReview }) {
  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div>
          <strong>{claim?.claim_id}</strong>
          <span style={{ color: 'var(--text-muted)', marginLeft: 8, fontSize: 13 }}>
            {claim?.member_name}
          </span>
          {type === 'appeal' ? (
            <span className="badge badge-submitted" style={{ marginLeft: 8, fontSize: 10 }}>Appeal</span>
          ) : (
            <span className="badge badge-manual" style={{ marginLeft: 8, fontSize: 10 }}>Manual Review</span>
          )}
        </div>
        <span className={`badge ${badgeClass[decision?.decision]}`}>{decision?.decision}</span>
      </div>

      <div style={{ marginTop: 12, display: 'flex', gap: 24, fontSize: 13 }}>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Amount: </span>
          <strong>₹{claim?.claim_amount?.toLocaleString()}</strong>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Confidence: </span>
          <ConfidenceMeter score={decision?.confidence_score} />
        </div>
      </div>

      {type === 'appeal' && (
        <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(235, 94, 85, 0.05)', borderRadius: 6, border: '1px solid rgba(235, 94, 85, 0.1)' }}>
          <div style={{ fontWeight: 600, color: 'var(--danger)', fontSize: 12, marginBottom: 4 }}>ORIGINAL SYSTEM DECISION: {decision?.decision}</div>
          {decision?.rejection_reasons?.length > 0 && (
            <div style={{ fontSize: 13, marginBottom: 2 }}>
              <strong>Rejection Reasons:</strong> {decision.rejection_reasons.join(', ')}
            </div>
          )}
          {decision?.notes && (
            <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              <strong>System Notes:</strong> {decision.notes}
            </div>
          )}
        </div>
      )}

      {type === 'appeal' && (
        <div style={{ marginTop: 10, padding: '10px 14px', background: 'rgba(9, 132, 227, 0.05)', borderRadius: 6, borderLeft: '4px solid var(--primary)' }}>
          <div style={{ fontWeight: 600, color: 'var(--primary)', fontSize: 12, marginBottom: 4 }}>APPEAL STATEMENT:</div>
          <div style={{ fontSize: 13, fontStyle: 'italic' }}>"{appealReason}"</div>
          {appealSupportingInfo && (
            <div style={{ fontSize: 12, marginTop: 4, color: 'var(--text-muted)' }}>
              <strong>Supporting Info:</strong> {appealSupportingInfo}
            </div>
          )}
        </div>
      )}

      {decision?.flags?.length > 0 && (
        <div style={{ marginTop: 8, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {decision.flags.map((f, i) => (
            <span key={i} className="badge badge-rejected" style={{ fontSize: 10 }}>⚠ {f}</span>
          ))}
        </div>
      )}

      {onReview && (
        <div style={{ marginTop: 12 }}>
          <button className="btn btn-primary" style={{ padding: '6px 14px', fontSize: 13 }} onClick={() => onReview(claim?.claim_id)}>
            Review
          </button>
        </div>
      )}
    </div>
  );
}
