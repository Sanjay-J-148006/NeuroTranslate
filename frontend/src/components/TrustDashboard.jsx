import ConfidenceGauge from './ConfidenceGauge'
import EntityHighlighter from './EntityHighlighter'
import GlossaryPanel from './GlossaryPanel'
import ExportButtons from './ExportButtons'

const LANG_LABELS = { ne: '🇳🇵 Nepali', si: '🇱🇰 Sinhala', en: '🇬🇧 English', unknown: '❓ Unknown' }
const MODEL_LABELS = { indictrans2: 'IndicTrans2 dist-200M', nllb: 'NLLB-200 dist-600M', passthrough: 'Pass-Through' }

function MetaRow({ label, value, badge, badgeClass }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
      <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{label}</span>
      {badge
        ? <span className={`badge ${badgeClass}`}>{value}</span>
        : <span style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: 13 }}>{value}</span>
      }
    </div>
  )
}

function SectionTitle({ children }) {
  return (
    <h3 style={{ fontSize: 14, fontWeight: 700, letterSpacing: '0.5px', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 16 }}>
      {children}
    </h3>
  )
}

export default function TrustDashboard({ job }) {
  if (!job) return null
  const {
    job_id, detected_language, language_confidence,
    translation_model, confidence_score, confidence_level,
    ner_entities, glossary_matches, ner_preservation_rate,
    glossary_preservation_rate, processing_time_seconds,
  } = job

  const langLabel = LANG_LABELS[detected_language] || detected_language
  const modelLabel = MODEL_LABELS[translation_model] || translation_model

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Confidence gauge */}
      <div className="glass fade-in-up" style={{ padding: 28, textAlign: 'center' }}>
        <SectionTitle>📊 Trust Score</SectionTitle>
        <ConfidenceGauge score={confidence_score} level={confidence_level} />

        <div className="divider" />

        {/* Signal breakdown bars */}
        {[
          { label: 'Translation Quality', value: (job.translation_confidence || 0) * 100, color: '#6c63ff' },
          { label: 'NER Preservation',    value: (ner_preservation_rate || 0) * 100,      color: '#a78bfa' },
          { label: 'Glossary Preservation',value:(glossary_preservation_rate || 0) * 100,  color: '#00d4ff' },
          { label: 'Language Confidence', value: (language_confidence || 0) * 100,         color: '#38ef7d' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ marginBottom: 12, textAlign: 'left' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{label}</span>
              <span style={{ fontSize: 12, fontWeight: 600, color }}>{value.toFixed(1)}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-bar-fill" style={{ width: `${value}%`, background: color }} />
            </div>
          </div>
        ))}
      </div>

      {/* Metadata */}
      <div className="glass fade-in-up" style={{ padding: 24 }}>
        <SectionTitle>🔎 Detection Details</SectionTitle>
        <MetaRow label="Detected Language" value={langLabel} badge badgeClass={`badge-${detected_language}`} />
        <MetaRow label="Language Confidence" value={`${((language_confidence || 0) * 100).toFixed(1)}%`} />
        <MetaRow label="Translation Model" value={modelLabel} />
        <MetaRow label="Processing Time" value={`${processing_time_seconds?.toFixed(2) || '—'} s`} />
      </div>

      {/* NER */}
      <div className="glass fade-in-up" style={{ padding: 24 }}>
        <SectionTitle>🛡️ Named Entities ({(ner_entities || []).length})</SectionTitle>
        <EntityHighlighter entities={ner_entities} />
      </div>

      {/* Glossary */}
      <div className="glass fade-in-up" style={{ padding: 24 }}>
        <SectionTitle>📖 Glossary Matches ({(glossary_matches || []).length})</SectionTitle>
        <GlossaryPanel matches={glossary_matches} />
      </div>

      {/* Export */}
      <div className="glass fade-in-up" style={{ padding: 24 }}>
        <SectionTitle>📥 Export Results</SectionTitle>
        <ExportButtons jobId={job_id} />
      </div>
    </div>
  )
}
