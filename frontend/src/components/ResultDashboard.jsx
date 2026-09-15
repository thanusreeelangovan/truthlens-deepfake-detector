import React from 'react'

export default function ResultDashboard({ result, onReset }) {
  const isManipulated = result.verdict === 'LIKELY_MANIPULATED'
  const totalFrames = result.frames_analyzed
  const verdictClass = result.verdict.toLowerCase().replaceAll('_', '-')

  return (
    <div className="result-report">
      <div className="report-heading"><div><p className="eyebrow">CASE / {result.case_id.slice(0, 8).toUpperCase()}</p><h2>FORENSIC REPORT</h2></div><button className="button button-quiet" onClick={onReset}>NEW CASE</button></div>
      <div className="result-lead"><div><p className="eyebrow">VIDEO VERDICT</p><div className={`verdict-label ${verdictClass}`}>{result.verdict.replaceAll('_', ' ')}</div><p className="report-caption">Probabilistic assessment from {result.model}.</p></div><ConfidenceRing value={result.confidence} fake={isManipulated} /></div>
      <div className="metric-grid"><div className="metric-box"><div className="value">{totalFrames}</div><div className="label">Frames analyzed</div></div><div className="metric-box"><div className="value">{result.faces_detected}</div><div className="label">Faces detected</div></div><div className="metric-box"><div className="value">{result.suspicious_frame_count}</div><div className="label">Suspicious frames</div></div></div>
      <div className="report-caption">Mean {Math.round(result.mean_probability * 100)}% · Median {Math.round(result.median_probability * 100)}% · Suspicious ratio {Math.round(result.suspicious_ratio * 100)}% · Longest sequence {result.longest_suspicious_sequence}</div>
      <div className="report-columns"><section><p className="section-title">EXPLANATION SIGNALS</p><ul className="flags-list">{result.explanation_signals.map((signal) => <li key={signal}><span className="flag-icon">+</span>{signal}</li>)}</ul></section><section><p className="section-title">FRAME PROBABILITIES</p><div className="probability-strip">{result.frame_probabilities.map(({ frame_index, fake_probability }) => <div className="probability" key={frame_index}><span>F{String(frame_index + 1).padStart(2, '0')}</span><i style={{ height: `${Math.max(8, fake_probability * 100)}%` }} className={fake_probability >= 0.65 ? 'suspicious' : ''} /><b>{Math.round(fake_probability * 100)}%</b></div>)}</div></section></div>
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
          stroke={fake ? 'var(--signal)' : 'var(--safe)'}
          strokeWidth="10"
          strokeDasharray={`${filled} ${circ - filled}`}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
        />
        <text x="70" y="64" textAnchor="middle" fontSize="28" fontWeight="700" fill={fake ? 'var(--signal)' : 'var(--safe)'}>
          {Math.round(value)}%
        </text>
        <text x="70" y="82" textAnchor="middle" fontSize="11" fill="var(--muted)">confidence</text>
      </svg>
    </div>
  )
}