import React, { useRef, useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function Uploader({ onJobStart }) {
  const inputRef = useRef()
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)

  const handleFile = async (file) => {
    if (!file) return
    setError(null)
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await axios.post(`${API}/upload`, form)
      onJobStart(data.job_id)
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed. Check the backend is running.')
    } finally {
      setUploading(false)
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  return (
    <div className="card">
      <div
        className={`upload-zone ${dragging ? 'drag-over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current.click()}
      >
        <div className="icon">🎬</div>
        <h2>Drop a video to analyze</h2>
        <p style={{ marginBottom: 20 }}>MP4, MOV, AVI, WEBM — up to 100 MB</p>
        <button className="btn btn-primary" disabled={uploading} onClick={e => { e.stopPropagation(); inputRef.current.click() }}>
          {uploading ? '⏳ Uploading…' : '📁 Choose file'}
        </button>
        <input ref={inputRef} type="file" accept="video/*" style={{ display: 'none' }} onChange={e => handleFile(e.target.files[0])} />
      </div>

      {/* Judge demo button */}
      <div style={{ marginTop: 16, textAlign: 'center' }}>
        <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 10 }}>
          Or run the pre-loaded demo video:
        </p>
        <button className="btn btn-ghost" onClick={async (e) => {
          e.stopPropagation()
          try {
            const { data } = await axios.get(`${API}/demo-start`)
            onJobStart(data.job_id)
          } catch {
            setError('No demo video found. Upload a video first.')
          }
        }}>
          ⚡ Run demo analysis
        </button>
      </div>

      {error && <p style={{ color: 'var(--red)', marginTop: 12, fontSize: 13 }}>⚠ {error}</p>}
    </div>
  )
}