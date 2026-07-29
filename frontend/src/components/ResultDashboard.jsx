import React, { useState } from 'react'

export default function ResultDashboard({ result, onReset }) {
  const isFake = result.verdict === 'FAKE'
  const [activeFrame, setActiveFrame] = useState(null)
  const totalFrames = result.frames_analyzed

  const flaggedSet = new Set(result.flagged_frames || [])

  return (
    <div>
      {/* Verdict card */}
      <div className="card" style={{ textAlign: 'center' }}>
        <p className="section-title">Analysis Complete</p>
        <div className={`verdict-badge ${isFake ? 'verdict-fake' : 'verdict-real'}`}
             style={{ margin: '0 auto 20px' }}>
          {isFake ? '⚠ DEEPFAKE DETECTED' : '✓ AUTHENTIC VIDEO'}
        </div>

        <ConfidenceRing value={result.confidence} fake={isFake} />

        <div className="metric-grid">
          <div className="metric-box">
            <div className="value" style={{ color: 'var(--accent)' }}>{totalFrames}</div>
            <div className="label">Frames analyzed</div>
          </div>
          <div className="metric-box">
            <div className="value">{result.faces_detected ?? 1}</div>
            <div className="label">Faces detected</div>
          </div>
          <div className="metric-box">
            <div className="value" style={{ color: isFake ? 'var(--red)' : 'var(--green)' }}>
              {result.flagged_frames?.length ?? 0}
            </div>
            <div className="label">Flagged frames</div>
          </div>
        </div>
      </div>

      {/* Distribution */}
      {result.frame_score_distribution && (
        <div className="card">
          <p className="section-title">Score distribution</p>
          <div className="metric-grid">
            <div className="metric-box">
              <div className="value" style={{ fontSize: 18, color: 'var(--amber)' }}>
                {(result.frame_score_distribution.mean * 100).toFixed(0)}%
              </div>
              <div className="label">Mean anomaly</div>
            </div>
            <div className="metric-box">
              <div className="value" style={{ fontSize: 18, color: 'var(--red)' }}>
                {(result.frame_score_distribution.max * 100).toFixed(0)}%
              </div>
              <div className="label">Peak anomaly</div>
            </div>
            <div className="metric-box">
              <div className="value" style={{ fontSize: 18, color: 'var(--accent)' }}>
                {(result.frame_score_distribution.p75 * 100).toFixed(0)}%
              </div>
              <div className="label">75th pct.</div>
            </div>
          </div>
        </div>
      )}

      {/* Why flagged */}
      {result.flags?.length > 0 && (
        <div className="card">
          <p className="section-title">Forensic findings</p>
          <ul className="flags-list">
            {result.flags.map((f, i) => (
              <li key={i}>
                <span className="flag-icon">!</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Frame strip */}
      <div className="card">
        <p className="section-title">Frame-level indicators</p>
        <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 12 }}>
          <span style={{ color: 'var(--red)' }}>■</span> Flagged &nbsp;&nbsp;
          <span style={{ color: 'var(--green)' }}>■</span> Clean
        </p>
        <div className="frame-strip">
          {Array.from({ length: totalFrames }, (_, i) => {
            const flagged = flaggedSet.has(i)
            return (
              <div
                key={i}
                className={`frame-thumb ${flagged ? 'flagged' : 'clean'}`}
                style={{ cursor: 'pointer', outline: activeFrame === i ? '2px solid var(--accent)' : 'none' }}
                onClick={() => setActiveFrame(activeFrame === i ? null : i)}
              >
                <span style={{ fontSize: 14 }}>{flagged ? '⚠' : '✓'}</span>
                <span className="frame-label">F{i + 1}</span>
              </div>
            )
          })}
        </div>
        {activeFrame !== null && (
          <div style={{
            marginTop: 12, padding: '10px 14px', background: 'var(--surface)',
            borderRadius: 8, fontSize: 13
          }}>
            Frame {activeFrame + 1}: {flaggedSet.has(activeFrame)
              ? <span style={{ color: 'var(--red)' }}>Anomaly detected</span>
              : <span style={{ color: 'var(--green)' }}>No anomaly detected</span>
            }
          </div>
        )}
      </div>

      <button className="btn btn-ghost" onClick={onReset} style={{ marginTop: 4 }}>
        ← Analyze another video
      </button>
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
        <circle cx="70" cy="70" r={r} fill="none"
          stroke={fake ? 'var(--red)' : 'var(--green)'}
          strokeWidth="10"
          strokeDasharray={`${filled} ${circ - filled}`}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
        />
        <text x="70" y="64" textAnchor="middle" fontSize="28" fontWeight="700"
              fill={fake ? 'var(--red)' : 'var(--green)'}>
          {Math.round(value)}%
        </text>
        <text x="70" y="82" textAnchor="middle" fontSize="11" fill="var(--text-dim)">
          confidence
        </text>
      </svg>
    </div>
  )
}