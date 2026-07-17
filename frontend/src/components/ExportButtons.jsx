import { getDownloadUrl } from '../services/api'

export default function ExportButtons({ jobId }) {
  if (!jobId) return null

  const formats = [
    { key: 'pdf',  label: 'Download PDF',  icon: '📄', color: '#f5576c' },
    { key: 'docx', label: 'Download DOCX', icon: '📝', color: '#6c63ff' },
    { key: 'txt',  label: 'Download TXT',  icon: '📃', color: '#38ef7d' },
  ]

  return (
    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
      {formats.map(({ key, label, icon, color }) => (
        <a
          key={key}
          href={getDownloadUrl(jobId, key)}
          download
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 7,
            padding: '10px 18px',
            borderRadius: 'var(--radius-sm)',
            background: `${color}18`,
            border: `1px solid ${color}44`,
            color,
            fontWeight: 600,
            fontSize: 13,
            textDecoration: 'none',
            transition: 'all 0.25s ease',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = `${color}30` }}
          onMouseLeave={e => { e.currentTarget.style.background = `${color}18` }}
        >
          <span style={{ fontSize: 16 }}>{icon}</span>
          {label}
        </a>
      ))}
    </div>
  )
}
