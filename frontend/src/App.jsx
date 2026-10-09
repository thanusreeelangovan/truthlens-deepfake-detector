/**
 * TruthLens AI — Root Shell
 * Path: frontend/src/App.jsx
 */

import { useEffect, useState } from 'react'
import { checkHealth } from './services/api'
import Uploader from './components/Uploader'
import ProgressPanel from './components/ProgressPanel'
import ResultDashboard from './components/ResultDashboard'

function App() {
  const [backendStatus, setBackendStatus] = useState('checking')
  const [activeCase, setActiveCase] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)

  useEffect(() => {
    checkHealth()
      .then((health) => setBackendStatus(health.model_loaded ? 'ready' : 'model-missing'))
      .catch(() => setBackendStatus('offline'))
  }, [])

  return (
    <div className="site-shell">
      <header className="topbar"><a className="brand" href="/">TRUTH<span>LENS</span></a><div className="top-meta"><span>MEDIA AUTHENTICATION SYSTEM</span><span className={`engine-dot ${backendStatus}`} /> <strong>ENGINE {backendStatus.toUpperCase()}</strong></div></header>
      {!activeCase && !analysisResult && <>
        <main className="hero-grid">
          <section className="hero-copy"><p className="eyebrow">TL / 001 / FORENSIC MEDIA UNIT</p><h1>Verify what<br /><em>your eyes</em> cannot.</h1><p className="hero-description">Frame level AI analysis for detecting manipulated and synthetic video content.</p><div className="hero-actions"><a className="button button-primary" href="#evidence">ANALYZE MEDIA <span>↘</span></a><a className="text-link" href="#pipeline">SEE HOW IT WORKS <span>→</span></a></div><div className="hero-readout"><span>{backendStatus === "ready" ? "● MODEL READY" : "● MODEL NOT READY"}</span><span>UTC {new Date().toISOString().slice(11, 19)}</span><span>BUILD 0.4.0</span></div></section>
          <section className="evidence-wrap" id="evidence"><Uploader disabled={backendStatus !== "ready"} onCaseOpened={setActiveCase} /><div className="evidence-meta"><span>INPUT / VIDEO</span><span>LOCAL MEDIA ANALYSIS</span><span>CASE ID GENERATED ON UPLOAD</span></div></section>
        </main>
        <section className="pipeline-section" id="pipeline"><div className="section-intro"><p className="eyebrow">ANALYSIS PIPELINE</p><h2>Every frame leaves<br />a trace.</h2></div><div className="pipeline-list">{['FRAME SAMPLING', 'FACE LOCALIZATION', 'FEATURE EXTRACTION', 'AUTHENTICITY INFERENCE', 'TEMPORAL AGGREGATION', 'VIDEO VERDICT'].map((step, index) => <div className="pipeline-step" key={step}><span>0{index + 1}</span><strong>{step}</strong><i>↗</i></div>)}</div></section>
        <section className="dossier"><div><p className="eyebrow">THE EXAMINATION</p><h2>Signals over<br />assumptions.</h2></div><div className="dossier-copy"><p>TruthLens inspects sampled frames, localizes faces, and compares model probabilities across time. The result is a confidence-aware assessment, not an absolute claim.</p><div className="dossier-lines"><span>FRAME LEVEL INSPECTION</span><span>TEMPORAL ANALYSIS</span><span>EXPLAINABLE RESULTS</span><span>CONFIDENCE AWARE DECISIONS</span></div></div></section>
        <footer className="footer-cta"><p className="eyebrow">READY FOR EXAMINATION</p><h2>Question the footage.<br /><em>Examine the evidence.</em></h2><a className="button button-primary" href="#evidence">START ANALYSIS <span>↘</span></a></footer>
      </>}
      {activeCase && !analysisResult && <main className="analysis-view"><ProgressPanel caseId={activeCase.case_id} onComplete={setAnalysisResult} onBack={() => setActiveCase(null)} /></main>}
      {analysisResult && <main className="analysis-view"><ResultDashboard result={analysisResult} onReset={() => { setActiveCase(null); setAnalysisResult(null) }} /></main>}
    </div>
  )
}

export default App