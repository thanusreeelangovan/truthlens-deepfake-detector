import React from 'react'

export default function ResultDashboard({ result, onReset }) {
  const isFake = result.verdict === 'FAKE'
  const totalFrames = result.frames_analyzed
  const flaggedCount = result.flagged_frames.length

  return (
    <div>
      <div className="card">
        <p className="section-title">Analysis Complete</p>

        <div className={`verdict-badge ${isFake ? 'verdict-fake' : 'verdict-real'}`}>
          {isFake ? '⚠ DEEPFAKE DETECTED' : '✓ AUTHENTIC VIDEO'}
        </div>

        <ConfidenceRing value={result.confidence} fake={isFake} />

        <div className="metric-grid">
          <div className="metric-box">
            <div className="value" style={{ color: 'var(--accent)' }}>{totalFrames}</div>
            <div className="label">Frames analyzed</div>
          </div>
          <div className="metric-box">
            <div className="value" style={{ color: 'var(--text)' }}>{result.faces_detected}</div>
            <div className="label">Faces detected</div>
          </div>
          <div className="metric-box">
            <div className="value" style={{ color: isFake ? 'var(--red)' : 'var(--green)' }}>{flaggedCount}</div>
            <div className="label">Flagged frames</div>
          </div>
        </div>
      </div>

      <div className="card">
        <p className="section-title">Why it was flagged</p>
        <ul className="flags-list">
          {result.flags.map((f, i) => (
            <li key={i}>
              <span className="flag-icon">!</span>
              {f}
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <p className="section-title">Frame-level indicators</p>
        <div className="frame-strip">
          {Array.from({ length: totalFrames }, (_, i) => {
            const flagged = result.flagged_frames.includes(i)
            return (
              <div key={i} className={`frame-thumb ${flagged ? 'flagged' : 'clean'}`}>
                <span>{flagged ? '⚠' : '✓'}</span>
                <span className="frame-label">F{i + 1}</span>
              </div>
            )
          })}
        </div>
      </div>

      <button className="btn btn-ghost" onClick={onReset}>← Analyze another video</button>
    </div>
  )
}

function ConfidenceRing({ value, fake }) {
  const r = 54
  const circ = 2 * Math.PI * r
  const filled = (value / 100) * circ

  return (
    <div className="confidence-ring-wrap">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={r} fill="none" stroke="var(--border)" strokeWidth="10" />
        <circle
          cx="70" cy="70" r={r}
          fill="none"
          stroke={fake ? 'var(--red)' : 'var(--green)'}
          strokeWidth="10"
          strokeDasharray={`${filled} ${circ - filled}`}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
        />
        <text x="70" y="64" textAnchor="middle" fontSize="28" fontWeight="700" fill={fake ? 'var(--red)' : 'var(--green)'}>
          {Math.round(value)}%
        </text>
        <text x="70" y="82" textAnchor="middle" fontSize="11" fill="var(--text-dim)">confidence</text>
      </svg>
    </div>
  )
}