export default function GlossaryPanel({ matches }) {
  if (!matches || matches.length === 0) {
    return (
      <p style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: '12px 0' }}>
        No glossary replacements applied.
      </p>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {matches.map((match, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(108,99,255,0.06)',
            border: '1px solid rgba(108,99,255,0.15)',
            fontSize: 13,
          }}
        >
          {/* Source term */}
          <span style={{ color: 'var(--text-secondary)', fontFamily: 'monospace', fontSize: 12 }}>
            {match.original_term}
          </span>

          {/* Arrow */}
          <span style={{ color: 'var(--accent)', fontWeight: 700, flexShrink: 0 }}>→</span>

          {/* Canonical term */}
          <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
            {match.replacement}
          </span>

          {/* Occurrences */}
          {match.occurrences > 1 && (
            <span style={{
              marginLeft: 'auto',
              padding: '2px 8px',
              background: 'rgba(108,99,255,0.2)',
              borderRadius: 100,
              fontSize: 11,
              color: 'var(--accent)',
              fontWeight: 600,
            }}>
              ×{match.occurrences}
            </span>
          )}
        </div>
      ))}
      <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
        {matches.length} term{matches.length !== 1 ? 's' : ''} enforced by glossary engine
      </p>
    </div>
  )
}
