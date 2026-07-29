import React, { useEffect, useRef, useState } from 'react'

const API = 'http://localhost:8000'

const STEP_ORDER = ['upload', 'extract', 'detect', 'analyze', 'score', 'done']
const STEP_LABELS = {
  upload: 'Video received',
  extract: 'Extracting frames',
  detect: 'Detecting faces',
  analyze: 'Running forensic analysis',
  score: 'Aggregating results',
  done: 'Analysis complete',
}

export default function ProgressPanel({ jobId, onComplete }) {
  const [pct, setPct] = useState(0)
  const [currentStep, setCurrentStep] = useState('upload')
  const [liveLabel, setLiveLabel] = useState('Starting analysis…')
  const [stepsDone, setStepsDone] = useState(new Set())
  const esRef = useRef(null)

  useEffect(() => {
    const es = new EventSource(`${API}/analyze/${jobId}`)
    esRef.current = es

    es.addEventListener('progress', (e) => {
      const data = JSON.parse(e.data)
      setPct(data.pct)
      setLiveLabel(data.label)
      setCurrentStep(data.step)

      if (data.pct >= 100) {
        const idx = STEP_ORDER.indexOf(data.step)
        setStepsDone(new Set(STEP_ORDER.slice(0, idx)))
      } else {
        const idx = STEP_ORDER.indexOf(data.step)
        setStepsDone(new Set(STEP_ORDER.slice(0, idx)))
      }
    })

    es.addEventListener('result', (e) => {
      const result = JSON.parse(e.data)
      es.close()
      setTimeout(() => onComplete(result), 500)
    })

    es.addEventListener('error', () => {
      setLiveLabel('Connection error — retrying…')
    })

    return () => es.close()
  }, [jobId])

  return (
    <div className="card">
      <p className="section-title">Forensic Analysis — Job {jobId?.slice(0, 8)}</p>
      <div className="progress-bar-track">
        <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <p style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 16 }}>
        {pct}% — {liveLabel}
      </p>
      <ul className="status-log">
        {STEP_ORDER.filter(s => s !== 'done').map((step) => {
          const done = stepsDone.has(step)
          const active = currentStep === step && pct < 100
          return (
            <li key={step} className={done ? 'done' : active ? 'active' : ''}>
              <span className={`dot ${done ? 'done' : active ? 'active' : ''}`} />
              {STEP_LABELS[step]}
              {done && <span style={{ marginLeft: 'auto', color: 'var(--green)' }}>✓</span>}
            </li>
          )
        })}
      </ul>
    </div>
  )
}