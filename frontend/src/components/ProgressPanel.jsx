import React, { useEffect, useState } from 'react'

const STEPS = [
  { id: 'upload',   label: 'Video received' },
  { id: 'extract',  label: 'Extracting frames…' },
  { id: 'detect',   label: 'Detecting faces…' },
  { id: 'analyze',  label: 'Running forensic analysis…' },
  { id: 'score',    label: 'Aggregating results…' },
]

export default function ProgressPanel({ jobId, onComplete }) {
  const [current, setCurrent] = useState(0)
  const [pct, setPct] = useState(0)

  useEffect(() => {
    // Week 1: simulate pipeline. Week 2: replace with real SSE
    const interval = setInterval(() => {
      setCurrent(c => {
        const next = c + 1
        setPct(Math.round((next / STEPS.length) * 100))
        if (next >= STEPS.length) {
          clearInterval(interval)
          setTimeout(() => onComplete(mockResult(jobId)), 600)
        }
        return next
      })
    }, 900)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="card">
      <p className="section-title">Forensic Analysis — Job {jobId?.slice(0, 8)}</p>
      <div className="progress-bar-track">
        <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <p style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 16 }}>{pct}% complete</p>
      <ul className="status-log">
        {STEPS.map((s, i) => (
          <li key={s.id} className={i < current ? 'done' : i === current ? 'active' : ''}>
            <span className={`dot ${i < current ? 'done' : i === current ? 'active' : ''}`} />
            {s.label}
            {i < current && <span style={{ marginLeft: 'auto', color: 'var(--green)' }}>✓</span>}
          </li>
        ))}
      </ul>
    </div>
  )
}

function mockResult(jobId) {
  return {
    job_id: jobId,
    verdict: 'FAKE',
    confidence: 87.4,
    frames_analyzed: 42,
    faces_detected: 1,
    flagged_frames: [3, 8, 14, 19, 27, 33],
    flags: [
      'Inconsistent lip movement detected in frames 8–14',
      'Face texture irregularities found around eye region',
      'Frame-to-frame temporal instability observed',
    ],
  }
}