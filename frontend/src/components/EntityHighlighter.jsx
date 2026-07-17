const LABEL_COLORS = {
  PER:  { bg: 'rgba(168,85,247,0.2)',  fg: '#c084fc', label: 'Person' },
  ORG:  { bg: 'rgba(59,130,246,0.2)',  fg: '#93c5fd', label: 'Org' },
  LOC:  { bg: 'rgba(16,185,129,0.2)',  fg: '#6ee7b7', label: 'Location' },
  DATE: { bg: 'rgba(245,158,11,0.2)',  fg: '#fcd34d', label: 'Date' },
  MISC: { bg: 'rgba(107,114,128,0.2)', fg: '#9ca3af', label: 'Misc' },
}

function EntityTag({ entity }) {
  const colors = LABEL_COLORS[entity.label] || LABEL_COLORS.MISC
  return (
    <div
      title={`${entity.label} — ${(entity.score * 100).toFixed(1)}% confidence`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: '4px 10px',
        borderRadius: 100,
        background: colors.bg,
        border: `1px solid ${colors.fg}44`,
        color: colors.fg,
        fontSize: 12,
        fontWeight: 600,
        cursor: 'default',
      }}
    >
      <span>{entity.text}</span>
      <span style={{
        padding: '1px 5px',
        background: `${colors.fg}22`,
        borderRadius: 4,
        fontSize: 10,
        letterSpacing: '0.5px',
        textTransform: 'uppercase',
      }}>
        {colors.label}
      </span>
    </div>
  )
}

export default function EntityHighlighter({ entities }) {
  if (!entities || entities.length === 0) {
    return (
      <p style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: '12px 0' }}>
        No named entities detected.
      </p>
    )
  }

  // Group by label
  const grouped = entities.reduce((acc, e) => {
    const key = e.label || 'MISC'
    if (!acc[key]) acc[key] = []
    acc[key].push(e)
    return acc
  }, {})

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {Object.entries(grouped).map(([label, group]) => {
        const colors = LABEL_COLORS[label] || LABEL_COLORS.MISC
        return (
          <div key={label}>
            <div style={{
              fontSize: 11,
              fontWeight: 700,
              color: colors.fg,
              letterSpacing: '1px',
              textTransform: 'uppercase',
              marginBottom: 8,
              display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: colors.fg }} />
              {colors.label} ({group.length})
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {group.map((e, i) => <EntityTag key={i} entity={e} />)}
            </div>
          </div>
        )
      })}
    </div>
  )
}
