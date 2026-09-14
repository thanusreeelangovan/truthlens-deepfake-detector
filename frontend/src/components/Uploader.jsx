import { useRef, useState } from 'react'
import { uploadVideo } from '../services/api'

export default function Uploader({ onCaseOpened }) {
  const inputRef = useRef()
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)

  const handleFile = async (file) => {
    if (!file) return
    setError(null)
    setUploading(true)
    try {
      const result = await uploadVideo(file)
      onCaseOpened(result)
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
    <div className="evidence-panel">
      <div
        className={`upload-zone ${dragging ? 'drag-over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current.click()}
      >
        <span className="eyebrow">CASE / NEW ANALYSIS</span>
        <div className="upload-mark">+</div>
        <h2>DROP MEDIA FOR FORENSIC EXAMINATION</h2>
        <p className="upload-copy">MP4 / MOV / AVI / WEBM <span>·</span> MAX 100 MB</p>
        <button className="button button-primary" disabled={uploading} type="button">
          {uploading ? 'UPLOADING EVIDENCE...' : 'SELECT EVIDENCE'}
        </button>
        <input ref={inputRef} type="file" accept="video/*" style={{ display: 'none' }} onChange={e => handleFile(e.target.files[0])} />
      </div>
      {error && <p className="error-message">{error}</p>}
    </div>
  )
}