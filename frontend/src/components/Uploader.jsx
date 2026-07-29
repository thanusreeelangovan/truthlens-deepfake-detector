/**
 * TruthLens AI — Uploader
 * Path: frontend/src/components/Uploader.jsx
 *
 * "Submit evidence" panel. Drag-and-drop or file picker.
 * Styled as a case-file intake form, not a generic upload widget.
 */

import { useState, useRef } from 'react'
import { uploadVideo } from '../services/api'

function Uploader({ onCaseOpened }) {
  const [isDragging, setIsDragging] = useState(false)
  const [progress, setProgress] = useState(null)
  const [error, setError] = useState(null)
  const [fileName, setFileName] = useState(null)
  const inputRef = useRef(null)

  const handleFile = async (file) => {
    if (!file) return
    setError(null)
    setFileName(file.name)
    setProgress(0)

    try {
      const result = await uploadVideo(file, setProgress)
      onCaseOpened(result)
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Submission failed. Evidence could not be logged.'
      )
      setProgress(null)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  return (
    <div className="w-full max-w-lg">
      <p className="exhibit-tag inline-block mb-4">Exhibit A — Submission</p>

      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`
          border cursor-pointer transition-colors duration-150
          bg-forensic-panel px-8 py-12 text-center
          ${isDragging ? 'border-forensic-safelight' : 'border-forensic-border'}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".mp4,.mov,.avi,.webm"
          className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}
        />

        {progress === null && (
          <>
            <p className="font-sans text-sm text-forensic-text mb-1">
              Drop video file or click to select
            </p>
            <p className="font-data text-xs text-forensic-muted">
              MP4 · MOV · AVI · WEBM — up to 100MB
            </p>
          </>
        )}

        {progress !== null && progress < 100 && (
          <div onClick={(e) => e.stopPropagation()}>
            <p className="font-data text-xs text-forensic-muted mb-3">
              LOGGING EVIDENCE — {fileName}
            </p>
            <div className="w-full h-1 bg-forensic-border">
              <div
                className="h-1 bg-forensic-safelight transition-all duration-150"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="font-data text-xs text-forensic-safelight mt-2">{progress}%</p>
          </div>
        )}

        {progress === 100 && (
          <p className="font-data text-xs text-forensic-real">
            CASE FILE OPENED — awaiting examination
          </p>
        )}
      </div>

      {error && (
        <p className="font-data text-xs text-forensic-fake mt-3">
          {error}
        </p>
      )}
    </div>
  )
}

export default Uploader