import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5 minutes for large files + slow CPU inference
})

export const uploadFile = async (file, enableNer, onUploadProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('enable_ner', enableNer ? 'true' : 'false')
  const res = await api.post('/translate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
  })
  return res.data // { job_id, status, message }
}

export const getJobStatus = async (jobId) => {
  const res = await api.get(`/jobs/${jobId}`)
  return res.data
}

export const getDownloadUrl = (jobId, format) =>
  `/api/download/${jobId}/${format}`

// ── Glossary API ──────────────────────────────────────────────────────────────

export const getGlossary = async () => {
  const res = await api.get('/glossary')
  return res.data
}

export const addGlossaryTerm = async (language, sourceTerm, targetTerm) => {
  const res = await api.post('/glossary', {
    language,
    source_term: sourceTerm,
    target_term: targetTerm,
  })
  return res.data
}

export const deleteGlossaryTerm = async (language, sourceTerm) => {
  const res = await api.delete(`/glossary/${language}/${encodeURIComponent(sourceTerm)}`)
  return res.data
}

// ── Sentence Edit API ─────────────────────────────────────────────────────────

export const editSentence = async (jobId, sentenceIndex, newTranslation) => {
  const res = await api.post(`/jobs/${jobId}/edit`, {
    sentence_index: sentenceIndex,
    new_translation: newTranslation,
  })
  return res.data
}

export default api
