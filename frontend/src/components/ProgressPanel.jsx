/**
 * TruthLens AI — ProgressPanel
 * Path: frontend/src/components/ProgressPanel.jsx
 *
 * Staged examiner view. Real backend call happens for "Extracting Frames";
 * remaining stages simulate progression until Day 4 wires them to real work.
 */

import { useEffect, useState } from 'react'
import { analyzeCase } from '../services/api'

const STAGES = [
  { key: 'extracting', label: 'Extracting frames' },
  { key: 'faces', label: 'Detecting faces' },
  { key: 'inference', label: 'Running authenticity inference' },
  { key: 'report', label: 'Compiling report' },
]

function ProgressPanel({ caseId, onComplete }) {
  const [stageIndex, setStageIndex] = useState(0)
  const [error, setError] = useState(null)
  const [meta, setMeta] = useState(null)

  useEffect(() => {
    let cancelled = false

    async function run() {
      try {
        const result = await analyzeCase(caseId)
        if (cancelled) return
        setMeta(result)
        setStageIndex(1)

        // Day 4 will replace this with real face-detection/inference calls.
        for (let i = 2; i <= STAGES.length; i++) {
          await new Promise((r) => setTimeout(r, 900))
          if (cancelled) return
          setStageIndex(i)
        }

        await new Promise((r) => setTimeout(r, 600))
        if (!cancelled) onComplete({ caseId, ...result })
      } catch (err) {
        if (!cancelled) {
          setError(err.response?.data?.detail || 'Examination failed.')
        }
      }
    }

    run()
    return () => { cancelled = true }
  }, [caseId])

  return (
    <div className="w-full max-w-lg">
      <p className="exhibit-tag inline-block mb-4">Examination in progress</p>

      <div className="filmstrip-edge scanning mb-6" />

      <div className="space-y-3">
        {STAGES.map((stage, i) => {
          const isDone = i < stageIndex
          const isActive = i === stageIndex
          return (
            <div key={stage.key} className="flex items-center gap-3">
              <span className={`
                w-1.5 h-1.5 flex-shrink-0
                ${isDone ? 'bg-forensic-real' : isActive ? 'bg-forensic-safelight animate-pulse' : 'bg-forensic-border'}
              `} />
              <span className={`
                font-data text-xs tracking-wide
                ${isDone ? 'text-forensic-real' : isActive ? 'text-forensic-safelight' : 'text-forensic-muted'}
              `}>
                {stage.label.toUpperCase()}
                {isDone ? ' — COMPLETE' : isActive ? '…' : ''}
              </span>
            </div>
          )
        })}
      </div>

      {meta && (
        <p className="font-data text-xs text-forensic-muted mt-6">
          {meta.sampled_frames} frames sampled from {meta.total_frames} total ({meta.fps} fps)
        </p>
      )}

      {error && (
        <p className="font-data text-xs text-forensic-fake mt-4">{error}</p>
      )}
    </div>
  )
}

export default ProgressPanel