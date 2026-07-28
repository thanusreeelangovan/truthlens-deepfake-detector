import React, { useState } from 'react'
import Uploader from './components/Uploader.jsx'
import ProgressPanel from './components/ProgressPanel.jsx'
import ResultDashboard from './components/ResultDashboard.jsx'

export default function App() {
  const [stage, setStage] = useState('idle') // idle | uploading | analyzing | done
  const [jobId, setJobId] = useState(null)
  const [result, setResult] = useState(null)

  return (
    <div className="app">
      <div className="logo">
        <div className="logo-icon">🔍</div>
        <div>
          <h1>Truth<span>Lens</span></h1>
          <div className="tagline">AI-powered deepfake forensic analysis</div>
        </div>
      </div>

      {stage === 'idle' && (
        <Uploader onJobStart={(id) => { setJobId(id); setStage('analyzing') }} />
      )}

      {stage === 'analyzing' && (
        <ProgressPanel jobId={jobId} onComplete={(r) => { setResult(r); setStage('done') }} />
      )}

      {stage === 'done' && (
        <ResultDashboard result={result} onReset={() => { setStage('idle'); setResult(null) }} />
      )}
    </div>
  )
}