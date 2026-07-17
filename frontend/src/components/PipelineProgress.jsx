const STAGES = [
  { key: 'parse',    label: 'Document Parsing',    icon: '📋' },
  { key: 'ocr',      label: 'OCR Extraction',       icon: '🔍' },
  { key: 'detect',   label: 'Language Detection',   icon: '🌐' },
  { key: 'translate',label: 'Translation',          icon: '🔄' },
  { key: 'glossary', label: 'Glossary Engine',      icon: '📖' },
  { key: 'ner',      label: 'NER Protection',       icon: '🛡️' },
  { key: 'score',    label: 'Confidence Scoring',   icon: '📊' },
  { key: 'export',   label: 'Exporting Results',    icon: '📥' },
]

function getStageStatus(stageIndex, jobStatus) {
  if (jobStatus === 'completed') return 'done'
  if (jobStatus === 'failed') return 'failed'
  if (jobStatus === 'processing') {
    // Approximate progress based on typical pipeline timing
    return stageIndex < 3 ? 'done' : stageIndex === 3 ? 'active' : 'pending'
  }
  return 'pending'
}

export default function PipelineProgress({ status }) {
  if (!status || status === 'pending') return null

  return (
    <div className="glass fade-in-up" style={{ padding: 28 }}>
      <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 20, color: 'var(--text-primary)' }}>
        🔬 Pipeline Progress
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {STAGES.map((stage, i) => {
          const stageStatus = getStageStatus(i, status)
          return (
            <div
              key={stage.key}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                background: stageStatus === 'active'
                  ? 'rgba(108,99,255,0.12)'
                  : stageStatus === 'done'
                  ? 'rgba(56,239,125,0.06)'
                  : 'transparent',
                border: `1px solid ${
                  stageStatus === 'active'
                    ? 'rgba(108,99,255,0.4)'
                    : stageStatus === 'done'
                    ? 'rgba(56,239,125,0.2)'
                    : 'transparent'
                }`,
                transition: 'all 0.3s ease',
              }}
            >
              {/* Status icon */}
              <div style={{ fontSize: 18, minWidth: 24, textAlign: 'center' }}>
                {stageStatus === 'done'    ? '✅' :
                 stageStatus === 'active'  ? <span className="spin" style={{ display:'inline-block', fontSize:14 }}>⚙️</span> :
                 stageStatus === 'failed'  ? '❌' : '⬜'}
              </div>

              {/* Stage emoji */}
              <span style={{ fontSize: 18 }}>{stage.icon}</span>

              {/* Label */}
              <span style={{
                fontSize: 14,
                fontWeight: stageStatus === 'active' ? 700 : 500,
                color: stageStatus === 'active'
                  ? 'var(--accent)'
                  : stageStatus === 'done'
                  ? 'var(--accent-green)'
                  : 'var(--text-muted)',
              }}>
                {stage.label}
              </span>

              {/* Active indicator */}
              {stageStatus === 'active' && (
                <div style={{ marginLeft: 'auto', display: 'flex', gap: 3 }}>
                  {[0,1,2].map(j => (
                    <div key={j} style={{
                      width: 5, height: 5, borderRadius: '50%',
                      background: 'var(--accent)',
                      animation: `pulse-glow 1s ease ${j * 0.2}s infinite`,
                    }} />
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
