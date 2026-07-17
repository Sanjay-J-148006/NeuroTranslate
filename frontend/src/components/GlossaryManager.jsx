import { useState, useEffect } from 'react'
import { toast } from 'react-hot-toast'
import { getGlossary, addGlossaryTerm, deleteGlossaryTerm } from '../services/api'

export default function GlossaryManager() {
  const [glossary, setGlossary] = useState({ ne: {}, si: {} })
  const [activeLang, setActiveLang] = useState('ne')
  const [newSource, setNewSource] = useState('')
  const [newTarget, setNewTarget] = useState('')
  const [loading, setLoading] = useState(false)

  const fetchGlossary = async () => {
    try {
      const data = await getGlossary()
      setGlossary(data)
    } catch (err) {
      console.error('Failed to load glossary:', err)
    }
  }

  useEffect(() => { fetchGlossary() }, [])

  const handleAdd = async () => {
    if (!newSource.trim() || !newTarget.trim()) {
      toast.error('Both source and target terms are required')
      return
    }
    setLoading(true)
    try {
      await addGlossaryTerm(activeLang, newSource.trim(), newTarget.trim())
      toast.success(`Added: ${newSource} → ${newTarget}`)
      setNewSource('')
      setNewTarget('')
      await fetchGlossary()
    } catch (err) {
      toast.error('Failed to add term')
    }
    setLoading(false)
  }

  const handleDelete = async (term) => {
    try {
      await deleteGlossaryTerm(activeLang, term)
      toast.success(`Removed: ${term}`)
      await fetchGlossary()
    } catch (err) {
      toast.error('Failed to remove term')
    }
  }

  const terms = glossary[activeLang] || {}
  const termEntries = Object.entries(terms)

  return (
    <div className="glass" style={{ padding: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>
          📖 Glossary Manager
        </h3>
        <div style={{ display: 'flex', gap: 4, background: 'var(--bg-card)', padding: 3, borderRadius: 8, border: '1px solid var(--border)' }}>
          {[
            { key: 'ne', label: '🇳🇵 Nepali' },
            { key: 'si', label: '🇱🇰 Sinhala' },
          ].map(lang => (
            <button
              key={lang.key}
              onClick={() => setActiveLang(lang.key)}
              style={{
                padding: '5px 12px', fontSize: 12, border: 'none', borderRadius: 6, cursor: 'pointer',
                background: activeLang === lang.key ? 'var(--accent)' : 'transparent',
                color: activeLang === lang.key ? '#fff' : 'var(--text-secondary)',
                fontWeight: 600, transition: 'all 0.2s',
              }}
            >
              {lang.label}
            </button>
          ))}
        </div>
      </div>

      {/* Add term form */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          type="text"
          placeholder="Source term..."
          value={newSource}
          onChange={e => setNewSource(e.target.value)}
          style={{
            flex: 1, padding: '8px 12px', borderRadius: 8,
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            color: 'var(--text-primary)', fontSize: 13, outline: 'none',
          }}
        />
        <input
          type="text"
          placeholder="English translation..."
          value={newTarget}
          onChange={e => setNewTarget(e.target.value)}
          style={{
            flex: 1, padding: '8px 12px', borderRadius: 8,
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            color: 'var(--text-primary)', fontSize: 13, outline: 'none',
          }}
        />
        <button
          onClick={handleAdd}
          disabled={loading}
          className="btn"
          style={{
            padding: '8px 16px', fontSize: 12, fontWeight: 700,
            background: 'var(--grad-primary)', color: '#fff', border: 'none',
            borderRadius: 8, cursor: 'pointer', whiteSpace: 'nowrap',
          }}
        >
          + Add
        </button>
      </div>

      {/* Term list */}
      <div style={{ maxHeight: 280, overflowY: 'auto' }}>
        {termEntries.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 24, fontSize: 13 }}>
            No terms in {activeLang === 'ne' ? 'Nepali' : 'Sinhala'} glossary yet. Add terms above.
          </div>
        ) : (
          termEntries.map(([source, target]) => (
            <div
              key={source}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '8px 12px', marginBottom: 4, borderRadius: 8,
                background: 'rgba(108, 99, 255, 0.05)', border: '1px solid rgba(108, 99, 255, 0.1)',
                transition: 'all 0.2s',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 0 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {source}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>→</span>
                <span style={{ fontSize: 13, color: 'var(--accent)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {target}
                </span>
              </div>
              <button
                onClick={() => handleDelete(source)}
                style={{
                  background: 'none', border: 'none', color: '#f5576c',
                  cursor: 'pointer', fontSize: 14, padding: '2px 6px',
                  borderRadius: 4, transition: 'background 0.2s',
                }}
                title="Remove term"
              >
                ✕
              </button>
            </div>
          ))
        )}
      </div>

      <div style={{ marginTop: 12, fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>
        {termEntries.length} term{termEntries.length !== 1 ? 's' : ''} • Changes apply to future translations
      </div>
    </div>
  )
}
