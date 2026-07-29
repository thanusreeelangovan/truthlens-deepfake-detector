/**
 * TruthLens AI — Root Shell
 * Path: frontend/src/App.jsx
 *
 * Day 1 scope: static shell + backend connectivity check.
 * Upload/progress/results components land Day 2+.
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

  return (
    <div className="min-h-screen bg-forensic-bg flex flex-col">
      <header className="border-b border-forensic-border px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-forensic-accent animate-pulse" />
          <h1 className="font-mono text-sm tracking-widest text-gray-300">
            TRUTHLENS<span className="text-forensic-accent">.AI</span>
          </h1>
        </div>
        <div className="font-mono text-xs text-forensic-muted">
          ENGINE:{' '}
          <span className={backendStatus === 'online' ? 'text-forensic-accent' : 'text-forensic-warn'}>
            {backendStatus.toUpperCase()}
          </span>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="font-mono text-xs text-forensic-muted tracking-widest mb-2">
            MEDIA FORENSICS PLATFORM
          </p>
          <h2 className="text-2xl text-gray-300 font-light">
            Upload interface arrives in Phase 1, Day 2
          </h2>
        </div>
      </main>
    </div>
  )
}

export default App