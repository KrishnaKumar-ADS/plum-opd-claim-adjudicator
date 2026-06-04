export default function ConfidenceMeter({ score = 0 }) {
  const pct = (score * 100).toFixed(1);
  const num = score * 100;
  const level = num >= 80 ? 'high' : num >= 60 ? 'medium' : 'low';

  return (
    <div className="confidence-meter">
      <div className="confidence-bar">
        <div className={`confidence-fill ${level}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="confidence-value">{pct}%</span>
    </div>
  );
}
