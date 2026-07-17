import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt', '.csv'],
  'image/*': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp'],
  'audio/*': ['.mp3', '.wav', '.m4a', '.ogg', '.flac'],
  'video/*': ['.mp4', '.avi', '.mov', '.mkv'],
}

const FORMAT_ICONS = [
  { label: 'PDF',   icon: '📄', color: '#f5576c' },
  { label: 'DOCX',  icon: '📝', color: '#6c63ff' },
  { label: 'Image', icon: '🖼️', color: '#00d4ff' },
  { label: 'Text',  icon: '📃', color: '#38ef7d' },
  { label: 'Audio', icon: '🎙️', color: '#f5a623' },
  { label: 'Video', icon: '🎥', color: '#f093fb' },
]

export default function UploadZone({ onFileSelected, isLoading }) {
  const [dragOver, setDragOver] = useState(false)

  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) onFileSelected(accepted[0])
  }, [onFileSelected])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
    disabled: isLoading,
  })

  return (
    <div style={{ width: '100%' }}>
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        style={{
          border: `2px dashed ${isDragActive ? 'var(--accent)' : 'var(--border)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: '48px 32px',
          textAlign: 'center',
          cursor: isLoading ? 'not-allowed' : 'pointer',
          background: isDragActive
            ? 'rgba(108, 99, 255, 0.08)'
            : 'var(--bg-card)',
          transition: 'all 0.25s ease',
          backdropFilter: 'blur(20px)',
          boxShadow: isDragActive ? '0 0 32px rgba(108,99,255,0.3)' : 'var(--shadow-card)',
        }}
      >
        <input {...getInputProps()} />

        <div style={{ fontSize: 56, marginBottom: 16, lineHeight: 1 }}>
          {isDragActive ? '📂' : '📤'}
        </div>

        <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8, color: 'var(--text-primary)' }}>
          {isDragActive ? 'Drop your file here' : 'Upload your document'}
        </h2>

        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 24 }}>
          Drag & drop or click to browse — up to 50 MB
        </p>

        {!isLoading && (
          <button className="btn btn-primary" type="button">
            Choose File
          </button>
        )}

        {isLoading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--accent)' }}>
            <div className="spin" style={{ width: 20, height: 20, border: '2px solid var(--accent)', borderTopColor: 'transparent', borderRadius: '50%' }} />
            <span style={{ fontWeight: 600 }}>Processing…</span>
          </div>
        )}
      </div>

      {/* Format badges */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', marginTop: 20 }}>
        {FORMAT_ICONS.map(({ label, icon, color }) => (
          <div
            key={label}
            style={{
              display: 'flex', alignItems: 'center', gap: 5,
              padding: '5px 12px',
              borderRadius: 100,
              background: `${color}18`,
              border: `1px solid ${color}44`,
              fontSize: 12,
              fontWeight: 600,
              color,
            }}
          >
            <span>{icon}</span> {label}
          </div>
        ))}
      </div>
    </div>
  )
}
