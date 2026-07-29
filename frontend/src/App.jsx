/**
 * TruthLens AI — Root Shell
 * Path: frontend/src/App.jsx
 *
 * Theme: "Evidence Locker" — darkroom / case-file forensic examiner,
 * not a hacker-terminal dashboard. Signature element is the sprocket-hole
 * filmstrip strip with a sweeping scan line during analysis.
 */

import { useEffect, useState } from 'react'
import axios from 'axios'

function App() {
  const [backendStatus, setBackendStatus] = useState('checking')

  useEffect(() => {
    axios.get('http://localhost:8000/api/health')
      .then(() => setBackendStatus('online'))
      .catch(() => setBackendStatus('offline'))
  }, [])

  const isScanning = backendStatus === 'checking'

  return (
    <div className="min-h-screen bg-forensic-bg flex flex-col">
      {/* Header — case file letterhead, not a nav bar */}
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

      {/* Signature element: filmstrip sprocket strip with scan line */}
      <div className={`filmstrip-edge ${isScanning ? 'scanning' : ''}`} />

      <main className="flex-1 flex items-center justify-center px-8">
        <div className="text-center max-w-md">
          <p className="exhibit-tag inline-block mb-4">Exhibit A — Pending</p>
          <h2 className="font-sans text-lg text-forensic-text font-medium mb-2">
            No media submitted for examination
          </h2>
          <p className="text-sm text-forensic-muted">
            Upload interface arrives in Phase 1, Day 2.
          </p>
        </div>
      </main>

      <div className="filmstrip-edge" />
    </div>
  )
}

export default App