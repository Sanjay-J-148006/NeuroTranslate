import { useState, useEffect, useRef } from 'react'
import { Toaster, toast } from 'react-hot-toast'
import UploadZone from './components/UploadZone'
import PipelineProgress from './components/PipelineProgress'
import TranslationView from './components/TranslationView'
import TrustDashboard from './components/TrustDashboard'
import GlossaryManager from './components/GlossaryManager'
import { uploadFile, getJobStatus } from './services/api'

const POLL_INTERVAL_MS = 2500

export default function App() {
  const [file, setFile] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [jobData, setJobData] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [activeTab, setActiveTab] = useState('translation') // 'translation' | 'dashboard' | 'glossary'
  const [enableNer, setEnableNer] = useState(true)
  const pollRef = useRef(null)

  // ── Polling ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!jobId) return
    const poll = async () => {
      try {
        const data = await getJobStatus(jobId)
        setJobData(data)
        if (data.status === 'completed') {
          clearInterval(pollRef.current)
          toast.success('Translation complete! 🎉')
          setIsUploading(false)
        } else if (data.status === 'failed') {
          clearInterval(pollRef.current)
          toast.error(`Pipeline failed: ${data.error_message || 'Unknown error'}`)
          setIsUploading(false)
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }
    pollRef.current = setInterval(poll, POLL_INTERVAL_MS)
    poll() // immediate first check
    return () => clearInterval(pollRef.current)
  }, [jobId])

  // ── Upload Handler ───────────────────────────────────────────────────────────
  const handleFileSelected = async (selectedFile) => {
    setFile(selectedFile)
    setJobData(null)
    setIsUploading(true)
    setUploadProgress(0)
    clearInterval(pollRef.current)

    const toastId = toast.loading(`Uploading ${selectedFile.name}…`)
    try {
      const res = await uploadFile(selectedFile, enableNer, (e) => {
        if (e.total) setUploadProgress(Math.round((e.loaded / e.total) * 100))
      })
      setJobId(res.job_id)
      toast.success('Uploaded! Pipeline running…', { id: toastId })
    } catch (err) {
      setIsUploading(false)
      const msg = err?.response?.data?.detail || err.message || 'Upload failed'
      toast.error(msg, { id: toastId })
    }
  }

  const handleReset = () => {
    clearInterval(pollRef.current)
    setFile(null)
    setJobId(null)
    setJobData(null)
    setIsUploading(false)
    setUploadProgress(0)
    setActiveTab('translation')
  }

  const handleTextUpdated = (newText) => {
    if (jobData) {
      setJobData({ ...jobData, translated_text: newText })
    }
  }

  const isCompleted = jobData?.status === 'completed'
  const isProcessing = isUploading || (jobData?.status === 'processing') || (jobData?.status === 'pending')

  return (
    <div style={{ minHeight: '100vh' }}>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#1a1a3e', color: '#f0f0ff', border: '1px solid rgba(108,99,255,0.3)' },
        }}
      />

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <header style={{
        borderBottom: '1px solid var(--border)',
        backdropFilter: 'blur(20px)',
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(10,10,26,0.85)',
      }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 38, height: 38,
              background: 'var(--grad-primary)',
              borderRadius: 10,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 20,
              boxShadow: '0 0 20px rgba(108,99,255,0.4)',
            }}>🧠</div>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800 }}>
                <span className="gradient-text">NeuroTranslate</span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', letterSpacing: '0.5px' }}>
                AI-POWERED MULTILINGUAL PIPELINE
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {isCompleted && (
              <span className="badge badge-high pulse-glow">✅ Completed</span>
            )}
            {isProcessing && (
              <span className="badge badge-moderate">⚙️ Processing</span>
            )}
            {file && (
              <button className="btn btn-secondary" style={{ fontSize: 12, padding: '6px 14px' }} onClick={handleReset}>
                ↩ New File
              </button>
            )}
          </div>
        </div>
      </header>

      {/* ── Main ────────────────────────────────────────────────────────────── */}
      <main style={{ maxWidth: 1280, margin: '0 auto', padding: '32px 24px' }}>

        {/* Hero — shown before upload */}
        {!file && (
          <div style={{ textAlign: 'center', marginBottom: 48 }} className="fade-in-up">
            <div style={{ fontSize: 13, fontWeight: 600, letterSpacing: '2px', color: 'var(--accent)', textTransform: 'uppercase', marginBottom: 16 }}>
              Hackathon Edition
            </div>
            <h1 style={{ fontSize: 'clamp(32px, 6vw, 56px)', fontWeight: 800, lineHeight: 1.15, marginBottom: 20 }}>
              Translate <span className="gradient-text">Nepali & Sinhala</span><br />documents instantly
            </h1>
            <p style={{ fontSize: 17, color: 'var(--text-secondary)', maxWidth: 560, margin: '0 auto 40px' }}>
              8-stage AI pipeline with OCR, NER protection, glossary enforcement, and a Trust Dashboard — supporting PDF, Image, DOCX, Audio & more.
            </p>

            {/* Feature pills */}
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', justifyContent: 'center', marginBottom: 48 }}>
              {[
                ['🇳🇵', 'NLLB-200', '#6c63ff'],
                ['🇱🇰', 'NLLB-200', '#00d4ff'],
                ['🔍', 'PaddleOCR', '#38ef7d'],
                ['🌐', 'FastText LID', '#f5a623'],
                ['🛡️', 'XLM-RoBERTa NER', '#f093fb'],
                ['📊', 'Confidence Score', '#f5576c'],
                ['🔒', 'PII Redaction', '#ff6b6b'],
                ['📖', 'Custom Glossary', '#4ecdc4'],
              ].map(([icon, label, color]) => (
                <div key={label + icon} style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '7px 14px', borderRadius: 100,
                  background: `${color}12`, border: `1px solid ${color}33`,
                  color, fontSize: 13, fontWeight: 600,
                }}>
                  {icon} {label}
                </div>
              ))}
            </div>

            {/* Glossary Manager on hero page */}
            <div style={{ maxWidth: 640, margin: '0 auto 32px' }}>
              <GlossaryManager />
            </div>

            {/* NER Enable/Disable Toggle */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 10,
              marginBottom: 24,
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(108, 99, 255, 0.15)',
              padding: '10px 20px',
              borderRadius: 12,
              width: 'fit-content',
              margin: '0 auto 24px'
            }}>
              <input
                type="checkbox"
                id="enableNerToggle"
                checked={enableNer}
                onChange={(e) => setEnableNer(e.target.checked)}
                style={{
                  cursor: 'pointer',
                  width: 18,
                  height: 18,
                  accentColor: 'var(--accent)'
                }}
              />
              <label htmlFor="enableNerToggle" style={{ cursor: 'pointer', fontSize: 14, fontWeight: 500, userSelect: 'none' }}>
                🔍 Verify Named Entities & PII (Names, Dates, Locations)
              </label>
            </div>

            <UploadZone onFileSelected={handleFileSelected} isLoading={false} />
          </div>
        )}

        {/* After upload */}
        {file && (
          <div style={{ display: 'grid', gridTemplateColumns: isCompleted ? '1fr 380px' : '1fr', gap: 24 }}>

            {/* Left column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

              {/* File info */}
              <div className="glass fade-in-up" style={{ padding: 20, display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ fontSize: 36 }}>
                  {file.type.includes('pdf') ? '📄' :
                   file.type.includes('image') ? '🖼️' :
                   file.type.includes('audio') ? '🎙️' :
                   file.type.includes('video') ? '🎥' :
                   file.name.endsWith('.docx') ? '📝' : '📃'}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: 15, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {file.name}
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                </div>
                {/* Upload progress */}
                {isUploading && uploadProgress < 100 && (
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent)', marginBottom: 4 }}>{uploadProgress}%</div>
                    <div style={{ width: 80 }}>
                      <div className="progress-bar">
                        <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }} />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Pipeline tracker */}
              <PipelineProgress status={jobData?.status} />

              {/* Tabs + Content */}
              {isCompleted && (
                <div className="fade-in-up">
                  {/* Tab bar */}
                  <div style={{ display: 'flex', gap: 2, marginBottom: 16, background: 'var(--bg-card)', padding: 4, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', width: 'fit-content' }}>
                    {[
                      { key: 'translation', label: '🔄 Translation' },
                      { key: 'dashboard',   label: '📊 Trust Score' },
                      { key: 'glossary',    label: '📖 Glossary' },
                    ].map(tab => (
                      <button
                        key={tab.key}
                        className="btn"
                        style={{
                          padding: '8px 18px', fontSize: 13,
                          background: activeTab === tab.key ? 'var(--grad-primary)' : 'transparent',
                          color: activeTab === tab.key ? '#fff' : 'var(--text-secondary)',
                          border: 'none',
                        }}
                        onClick={() => setActiveTab(tab.key)}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  {activeTab === 'translation' && (
                    <TranslationView
                      sourceText={jobData.source_text}
                      translatedText={jobData.translated_text}
                      detectedLanguage={jobData.detected_language}
                      sentencePairs={jobData.sentence_pairs}
                      jobId={jobId}
                      onTextUpdated={handleTextUpdated}
                    />
                  )}
                  {activeTab === 'dashboard' && (
                    <TrustDashboard job={jobData} />
                  )}
                  {activeTab === 'glossary' && (
                    <GlossaryManager />
                  )}
                </div>
              )}

              {/* Upload another */}
              {isProcessing && (
                <div className="glass" style={{ padding: 24 }}>
                  <UploadZone onFileSelected={handleFileSelected} isLoading={true} />
                </div>
              )}
            </div>

            {/* Right column — Trust Dashboard sidebar when completed */}
            {isCompleted && (
              <div className="fade-in-up">
                <TrustDashboard job={jobData} />
              </div>
            )}
          </div>
        )}
      </main>

      {/* ── Footer ──────────────────────────────────────────────────────────── */}
      <footer style={{ borderTop: '1px solid var(--border)', padding: '20px 24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12, marginTop: 48 }}>
        NeuroTranslate · AI Translation Pipeline · Makeathon Edition ·{' '}
        <span className="gradient-text" style={{ fontWeight: 600 }}>Built with FastAPI + React</span>
      </footer>
    </div>
  )
}
