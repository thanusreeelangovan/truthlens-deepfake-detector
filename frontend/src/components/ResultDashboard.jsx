import React from 'react'

export default function ResultDashboard({ result, onReset }) {
  const isManipulated = result.verdict === 'LIKELY_MANIPULATED'
  const totalFrames = result.frames_analyzed
  const verdictClass = result.verdict.toLowerCase().replaceAll('_', '-')
  const downloadReport = () => {
    const report = {
      case_id: result.case_id,
      verdict: result.verdict,
      model: result.model,
      model_source: result.model_source,
      research_reference_model: result.research_reference_model,
      confidence_calibrated: false,
      decision_policy: result.decision_policy,
      screening_signal: result.screening_signal,
      decision_reason_code: result.decision_reason_code,
      frame_quality: result.frame_quality,
      analyzed_frames: result.frames_analyzed,
      frame_probabilities: result.frame_probabilities,
      mean_probability: result.mean_probability,
      median_probability: result.median_probability,
      suspicious_ratio: result.suspicious_ratio,
      explanation_signals: result.explanation_signals,
      disclaimer: 'Model predictions are not forensic proof and are not calibrated probabilities of authenticity.',
    }
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.href = url
    link.download = `truthlens-${result.case_id.slice(0, 8)}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="result-report">
      <div className="report-heading"><div><p className="eyebrow">CASE / {result.case_id.slice(0, 8).toUpperCase()}</p><h2>FORENSIC REPORT</h2></div><div><button className="button button-quiet" onClick={downloadReport}>DOWNLOAD JSON REPORT</button><button className="button button-quiet" onClick={onReset}>NEW CASE</button></div></div>
      <div className="result-lead"><div><p className="eyebrow">VIDEO VERDICT</p><div className={`verdict-label ${verdictClass}`}>{result.verdict.replaceAll('_', ' ')}</div><p className="report-caption">Experimental frame model signals from {result.model}. Not a verified authenticity assessment.</p></div><ConfidenceRing value={result.frames_analyzed ? result.mean_probability : null} fake={isManipulated} /></div>
      {result.research_reference_model && <p className="report-caption">Research reference model by Himanshu Kashyap (Xicor9), trained externally on FaceForensics++ C23. Not trained or validated by TruthLens. Results are experimental and not forensic proof. <a href="https://huggingface.co/Xicor9/efficientnet-b0-ffpp-c23" target="_blank" rel="noreferrer">Model attribution</a>.</p>}
      {result.screening_signal && <section style={{marginBottom: "1.5rem", padding: "1rem", border: "1px solid var(--border)"}}>
        <p className="eyebrow">EXPERIMENTAL SCREENING SIGNAL</p>
        <p style={{fontSize: "1.1rem", fontWeight: 700}}>{result.screening_signal.replaceAll("_", " ")}</p>
        <p className="report-caption">The research model is not validated for general uploads. Elevated scores alone do not establish manipulation. No definitive fake or authentic verdict is issued.</p>
      </section>}
      {result.frame_quality?.near_static_video && <p className="report-caption">Very little visual change between sampled frames. This input cannot provide meaningful temporal evidence.</p>}
      <div className="metric-grid"><div className="metric-box"><div className="value">{totalFrames}</div><div className="label">Frames analyzed</div></div><div className="metric-box"><div className="value">{result.faces_detected}</div><div className="label">Faces detected</div></div><div className="metric-box"><div className="value">{result.suspicious_frame_count}</div><div className="label">Suspicious frames</div></div></div>
      <div className="report-caption">Uncalibrated model scores, not forensic confidence. Mean {Math.round(result.mean_probability * 100)}% · Median {Math.round(result.median_probability * 100)}% · Suspicious ratio {Math.round(result.suspicious_ratio * 100)}% · Longest sequence {result.longest_suspicious_sequence}</div>
      <div className="report-columns"><section><p className="section-title">EXPLANATION SIGNALS</p><ul className="flags-list">{result.explanation_signals.map((signal) => <li key={signal}><span className="flag-icon">+</span>{signal}</li>)}</ul></section><section><p className="section-title">FRAME PROBABILITIES</p><div className="probability-strip">{result.frame_probabilities.map(({ frame_index, timestamp_seconds, fake_probability }) => <div className="probability" key={frame_index}><span>{timestamp_seconds == null ? `F${frame_index + 1}` : `${Number(timestamp_seconds).toFixed(1)}s`}</span><i style={{ height: `${Math.max(8, fake_probability * 100)}%` }} className={fake_probability >= 0.65 ? 'suspicious' : ''} /><b>{Math.round(fake_probability * 100)}%</b></div>)}</div></section></div>
    </div>
  )
}

function ConfidenceRing({ value, fake }) {
  const r = 54
  const circ = 2 * Math.PI * r
  const filled = (value ?? 0) * circ

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
          {value == null ? "N/A" : Number(value).toFixed(2)}
        </text>
        <text x="70" y="82" textAnchor="middle" fontSize="11" fill="var(--muted)">raw model score</text>
      </svg>
    </div>
  )
}