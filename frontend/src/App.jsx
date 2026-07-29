/**
 * TruthLens AI — Root Shell
 * Path: frontend/src/App.jsx
 */

import { useEffect, useState } from 'react'
import { checkHealth } from './services/api'
import Uploader from './components/Uploader'
import ProgressPanel from './components/ProgressPanel'

function App() {
  const [backendStatus, setBackendStatus] = useState('checking')
  const [activeCase, setActiveCase] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)

  useEffect(() => {
    checkHealth()
      .then(() => setBackendStatus('online'))
      .catch(() => setBackendStatus('offline'))
  }, [])

  const isScanning = backendStatus === 'checking'

  return (
    <div className="min-h-screen bg-forensic-bg flex flex-col">
      <header className="px-8 pt-6 pb-4 flex items-end justify-between">
        <div>
          <p className="exhibit-tag mb-1">Case File — Media Authentication</p>
          <h1 className="font-stamp text-2xl text-forensic-text tracking-wide">
            TruthLens<span className="text-forensic-safelight">.</span>AI
          </h1>
        </div>
        <div className="font-data text-xs text-right">
          <p className="text-forensic-muted">EXAMINER ENGINE</p>
          <p className={
            backendStatus === 'online' ? 'text-forensic-real' :
            backendStatus === 'offline' ? 'text-forensic-fake' :
            'text-forensic-safelight'
          }>
            {backendStatus.toUpperCase()}
          </p>
        </div>
      </header>

      <div className={`filmstrip-edge ${isScanning ? 'scanning' : ''}`} />

      <main className="flex-1 flex items-center justify-center px-8">
        {!activeCase && (
          <Uploader onCaseOpened={setActiveCase} />
        )}

        {activeCase && !analysisResult && (
          <ProgressPanel caseId={activeCase.case_id} onComplete={setAnalysisResult} />
        )}

        {analysisResult && (
          <div className="text-center max-w-md">
            <p className="exhibit-tag inline-block mb-4">
              Case {analysisResult.case_id.slice(0, 8)} — Examined
            </p>
            <h2 className="font-sans text-lg text-forensic-text font-medium mb-2">
              {analysisResult.sampled_frames} frames processed
            </h2>
            <p className="text-sm text-forensic-muted">
              Authenticity report dashboard arrives in Phase 1, Day 4.
            </p>
          </div>
        )}
      </main>

      <div className="filmstrip-edge" />
    </div>
  )
}

export default App