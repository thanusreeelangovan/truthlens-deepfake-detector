/**
 * TruthLens AI — ProgressPanel
 * Path: frontend/src/components/ProgressPanel.jsx
 *
 * The backend performs all stages in one request. This panel never invents
 * progress with timers while waiting for the returned report.
 */

import { useEffect, useState } from 'react'
import { analyzeCase } from '../services/api'

function ProgressPanel({ caseId, onComplete }) {
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    async function run() {
      try {
        const result = await analyzeCase(caseId)
        if (cancelled) return


        if (!cancelled) onComplete(result)
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
    <div>
      <p className="eyebrow">EXAMINATION IN PROGRESS</p>

      <div className="scan-line" />



      <div className="stage-list">
        {['FRAME SAMPLING', 'FACE LOCALIZATION', 'FEATURE EXTRACTION', 'AUTHENTICITY INFERENCE', 'TEMPORAL AGGREGATION', 'VIDEO VERDICT'].map((label) => (
          <div className="stage-row active" key={label}>
            <span className="stage-dot" />
            <span>{label}</span>
            <strong>RUNNING</strong>
          </div>
        ))}
      </div>
      <p className="progress-note">Sampling and inference are performed on the server. This panel will resolve when the complete report is returned.</p>
      {error && <p className="error-message">{error}</p>}
    </div>
  )
}

export default ProgressPanel