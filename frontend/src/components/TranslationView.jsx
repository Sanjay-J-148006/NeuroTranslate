import { useState, useRef, useCallback } from 'react'
import { toast } from 'react-hot-toast'
import { editSentence } from '../services/api'

const CONFIDENCE_COLORS = {
  high:     { bg: 'rgba(56, 239, 125, 0.08)', border: 'rgba(56, 239, 125, 0.3)', dot: '#38ef7d' },
  moderate: { bg: 'rgba(245, 166, 35, 0.08)', border: 'rgba(245, 166, 35, 0.3)', dot: '#f5a623' },
  low:      { bg: 'rgba(245, 87, 108, 0.08)', border: 'rgba(245, 87, 108, 0.3)', dot: '#f5576c' },
}

function getConfLevel(conf) {
  if (conf >= 0.85) return 'high'
  if (conf >= 0.6)  return 'moderate'
  return 'low'
}

export default function TranslationView({ sourceText, translatedText, detectedLanguage, sentencePairs, jobId, onTextUpdated }) {
  const [editingIdx, setEditingIdx] = useState(null)
  const [editValue, setEditValue] = useState('')
  const [saving, setSaving] = useState(false)
  const [showAnonymized, setShowAnonymized] = useState(false)
  const [localPairs, setLocalPairs] = useState(sentencePairs || [])

  const sourceRef = useRef(null)
  const targetRef = useRef(null)

  // Synchronized scrolling
  const handleScroll = useCallback((source) => {
    if (!sourceRef.current || !targetRef.current) return
    const from = source === 'left' ? sourceRef.current : targetRef.current
    const to   = source === 'left' ? targetRef.current : sourceRef.current
    const ratio = from.scrollTop / (from.scrollHeight - from.clientHeight || 1)
    to.scrollTop = ratio * (to.scrollHeight - to.clientHeight || 1)
  }, [])

  const handleEditStart = (idx, currentText) => {
    setEditingIdx(idx)
    setEditValue(currentText)
  }

  const handleEditSave = async () => {
    if (editingIdx === null) return
    setSaving(true)
    try {
      const res = await editSentence(jobId, editingIdx, editValue)
      // Update local pairs
      const updated = [...localPairs]
      updated[editingIdx] = { ...updated[editingIdx], translated: editValue, confidence: 1.0 }
      setLocalPairs(updated)
      if (onTextUpdated) onTextUpdated(res.translated_text)
      toast.success('Sentence updated & exports regenerated!')
      setEditingIdx(null)
    } catch (err) {
      toast.error('Failed to save edit')
    }
    setSaving(false)
  }

  const handleEditCancel = () => {
    setEditingIdx(null)
    setEditValue('')
  }

  const pairs = localPairs.length > 0 ? localPairs : []
  const hasPairs = pairs.length > 0

  // Stats
  const highCount = pairs.filter(p => getConfLevel(p.confidence) === 'high').length
  const modCount  = pairs.filter(p => getConfLevel(p.confidence) === 'moderate').length
  const lowCount  = pairs.filter(p => getConfLevel(p.confidence) === 'low').length

  const langLabel = detectedLanguage === 'ne' ? '🇳🇵 Nepali' : detectedLanguage === 'si' ? '🇱🇰 Sinhala' : '🌐 ' + (detectedLanguage || 'Unknown')

  return (
    <div className="glass" style={{ padding: 0, overflow: 'hidden' }}>

      {/* ── Toolbar ───────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10,
        padding: '12px 20px', borderBottom: '1px solid var(--border)', background: 'rgba(108,99,255,0.03)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 13, fontWeight: 700 }}>{langLabel} → 🇬🇧 English</span>
          {hasPairs && (
            <div style={{ display: 'flex', gap: 8, fontSize: 11, fontWeight: 600 }}>
              <span style={{ color: '#38ef7d' }}>● {highCount} High</span>
              <span style={{ color: '#f5a623' }}>● {modCount} Medium</span>
              <span style={{ color: '#f5576c' }}>● {lowCount} Low</span>
            </div>
          )}
        </div>

        {/* Offline badge */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6, padding: '4px 12px',
          borderRadius: 100, background: 'rgba(56,239,125,0.1)', border: '1px solid rgba(56,239,125,0.3)',
          fontSize: 11, fontWeight: 700, color: '#38ef7d',
        }}>
          🔒 100% Offline · Zero Data Leakage
        </div>
      </div>

      {/* ── Split View ────────────────────────────────────────────────── */}
      {hasPairs ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: 400 }}>
          {/* Source column header */}
          <div style={{
            padding: '10px 20px', fontSize: 12, fontWeight: 700, color: 'var(--text-muted)',
            borderBottom: '1px solid var(--border)', borderRight: '1px solid var(--border)',
            background: 'rgba(108,99,255,0.04)', textTransform: 'uppercase', letterSpacing: 1,
          }}>
            Source Text
          </div>
          <div style={{
            padding: '10px 20px', fontSize: 12, fontWeight: 700, color: 'var(--text-muted)',
            borderBottom: '1px solid var(--border)',
            background: 'rgba(108,99,255,0.04)', textTransform: 'uppercase', letterSpacing: 1,
          }}>
            Translated Text · Click to edit
          </div>

          {/* Source sentences */}
          <div
            ref={sourceRef}
            onScroll={() => handleScroll('left')}
            style={{
              padding: 16, maxHeight: 500, overflowY: 'auto',
              borderRight: '1px solid var(--border)',
            }}
          >
            {pairs.map((pair, idx) => (
              <div
                key={`src-${idx}`}
                id={`src-${idx}`}
                style={{
                  padding: '10px 14px', marginBottom: 6, borderRadius: 8,
                  background: editingIdx === idx ? 'rgba(108,99,255,0.15)' : 'rgba(255,255,255,0.02)',
                  border: `1px solid ${editingIdx === idx ? 'var(--accent)' : 'transparent'}`,
                  fontSize: 13, lineHeight: 1.6, color: 'var(--text-primary)',
                  transition: 'all 0.2s',
                }}
              >
                {pair.source}
              </div>
            ))}
          </div>

          {/* Translated sentences */}
          <div
            ref={targetRef}
            onScroll={() => handleScroll('right')}
            style={{ padding: 16, maxHeight: 500, overflowY: 'auto' }}
          >
            {pairs.map((pair, idx) => {
              const level = getConfLevel(pair.confidence)
              const colors = CONFIDENCE_COLORS[level]
              const isEditing = editingIdx === idx

              return (
                <div
                  key={`tgt-${idx}`}
                  id={`tgt-${idx}`}
                  style={{
                    padding: '10px 14px', marginBottom: 6, borderRadius: 8,
                    background: colors.bg, border: `1px solid ${colors.border}`,
                    fontSize: 13, lineHeight: 1.6, cursor: 'pointer',
                    transition: 'all 0.2s', position: 'relative',
                  }}
                  onClick={() => !isEditing && handleEditStart(idx, pair.translated)}
                >
                  {/* Confidence dot */}
                  <span style={{
                    position: 'absolute', top: 6, right: 8, width: 8, height: 8,
                    borderRadius: '50%', background: colors.dot,
                    boxShadow: `0 0 6px ${colors.dot}`,
                  }} title={`Confidence: ${Math.round(pair.confidence * 100)}%`} />

                  {isEditing ? (
                    <div>
                      <textarea
                        value={editValue}
                        onChange={e => setEditValue(e.target.value)}
                        autoFocus
                        style={{
                          width: '100%', minHeight: 60, padding: 8, borderRadius: 6,
                          background: 'var(--bg-card)', border: '1px solid var(--accent)',
                          color: 'var(--text-primary)', fontSize: 13, resize: 'vertical',
                          fontFamily: 'inherit', outline: 'none',
                        }}
                      />
                      <div style={{ display: 'flex', gap: 6, marginTop: 6, justifyContent: 'flex-end' }}>
                        <button onClick={handleEditCancel} style={{
                          padding: '4px 12px', fontSize: 11, border: '1px solid var(--border)',
                          borderRadius: 6, background: 'transparent', color: 'var(--text-secondary)',
                          cursor: 'pointer',
                        }}>Cancel</button>
                        <button onClick={handleEditSave} disabled={saving} style={{
                          padding: '4px 12px', fontSize: 11, border: 'none', borderRadius: 6,
                          background: 'var(--accent)', color: '#fff', cursor: 'pointer', fontWeight: 700,
                        }}>{saving ? 'Saving...' : '✓ Save'}</button>
                      </div>
                    </div>
                  ) : (
                    <span style={{ color: 'var(--text-primary)' }}>{pair.translated}</span>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      ) : (
        /* Fallback: simple source/translated view when no sentence pairs */
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: 300 }}>
          <div style={{ padding: 20, borderRight: '1px solid var(--border)' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>Source</div>
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.7, color: 'var(--text-primary)', margin: 0, fontFamily: 'inherit' }}>
              {sourceText}
            </pre>
          </div>
          <div style={{ padding: 20 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>Translated</div>
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.7, color: 'var(--text-primary)', margin: 0, fontFamily: 'inherit' }}>
              {translatedText}
            </pre>
          </div>
        </div>
      )}

      {/* ── Legend ─────────────────────────────────────────────────────── */}
      {hasPairs && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20,
          padding: '10px 20px', borderTop: '1px solid var(--border)',
          fontSize: 11, color: 'var(--text-muted)', background: 'rgba(108,99,255,0.02)',
        }}>
          <span>🟢 High confidence (&gt;85%)</span>
          <span>🟡 Moderate (60-85%)</span>
          <span>🔴 Low (&lt;60%) — review recommended</span>
          <span>📝 Click any sentence to edit</span>
        </div>
      )}
    </div>
  )
}
