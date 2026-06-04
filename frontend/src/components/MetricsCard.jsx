export default function MetricsCard({ title, value, subtitle, color, icon, trend }) {
  return (
    <div className="stat-card" style={{ position: 'relative', overflow: 'hidden' }}>
      {icon && (
        <div style={{
          position: 'absolute', top: 12, right: 16,
          fontSize: 28, opacity: 0.15, userSelect: 'none',
        }}>
          {icon}
        </div>
      )}
      <div className="stat-value" style={color ? { color } : {}}>{value}</div>
      <div className="stat-label">{title}</div>
      {subtitle && (
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{subtitle}</div>
      )}
      {trend != null && (
        <div style={{
          fontSize: 11,
          color: trend > 0 ? 'var(--success)' : trend < 0 ? 'var(--danger)' : 'var(--text-muted)',
          marginTop: 4,
          fontWeight: 600,
        }}>
          {trend > 0 ? `↑ ${trend}%` : trend < 0 ? `↓ ${Math.abs(trend)}%` : '—'}
        </div>
      )}
    </div>
  );
}
