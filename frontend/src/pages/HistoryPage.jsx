import { motion } from 'framer-motion'
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  CloudRain,
  CloudSun,
  LoaderCircle,
  ListRestart,
  RefreshCcw,
  Trash2,
  X,
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import SectionHeader from '../components/SectionHeader'
import {
  clearPredictionHistory,
  deletePredictionHistory,
  fetchPredictionHistory,
} from '../services/historyApi'
import { getDisplayRiskLevel } from '../utils/predictionResult'

const riskStyles = {
  Low: 'border-emerald-300/20 bg-emerald-300/10 text-emerald-100',
  Moderate: 'border-amber-300/20 bg-amber-300/10 text-amber-100',
  High: 'border-rose-300/20 bg-rose-300/10 text-rose-100',
}

function formatCreatedAt(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatObservationDate(value) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(
    new Date(`${value}T00:00:00`),
  )
}

function formatProbability(value) {
  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 1,
    minimumFractionDigits: 0,
  }).format(value * 100)
}

function LoadingHistory() {
  return (
    <section
      className="glass-panel mt-10 rounded-[1.75rem] p-6 sm:p-8"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="flex items-center gap-3">
        <LoaderCircle aria-hidden="true" className="animate-spin text-cyan-200" size={22} />
        <div>
          <h2 className="font-extrabold text-white">Loading prediction history</h2>
          <p className="mt-1 text-sm text-slate-400">Retrieving your saved RainWise outlooks.</p>
        </div>
      </div>
      <div className="mt-7 grid gap-4" aria-hidden="true">
        {[0, 1].map((item) => (
          <div key={item} className="h-40 animate-pulse rounded-2xl bg-white/[0.045]" />
        ))}
      </div>
    </section>
  )
}

function EmptyHistory() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel relative mt-10 grid min-h-[28rem] place-items-center overflow-hidden rounded-[1.75rem] p-7 text-center"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(66,190,255,0.08),transparent_42%)]" />
      <div className="relative max-w-md">
        <div className="relative mx-auto grid size-24 place-items-center rounded-[2rem] border border-sky-200/15 bg-sky-300/10 text-cyan-200">
          <Clock3 aria-hidden="true" size={39} strokeWidth={1.5} />
          <span className="absolute -bottom-2 -right-2 grid size-10 place-items-center rounded-xl border-4 border-[#0b1b30] bg-slate-100 text-slate-700">
            <CloudRain aria-hidden="true" size={19} />
          </span>
        </div>
        <h2 className="mt-9 text-2xl font-extrabold tracking-tight text-white">No predictions yet.</h2>
        <p className="mt-3 text-sm leading-7 text-slate-400">
          Successful rainfall outlooks will appear here automatically after you submit the prediction form.
        </p>
        <Link to="/predict" className="secondary-button mt-7">
          Create a prediction <ArrowRight aria-hidden="true" size={17} />
        </Link>
      </div>
    </motion.section>
  )
}

function HistoryError({ message, onRetry }) {
  return (
    <section className="mt-10 rounded-[1.75rem] border border-rose-300/20 bg-rose-300/[0.055] p-7 sm:p-9" role="alert">
      <div className="mx-auto max-w-lg text-center">
        <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-rose-300/10 text-rose-200">
          <AlertTriangle aria-hidden="true" size={25} />
        </span>
        <h2 className="mt-5 text-xl font-extrabold text-white">Prediction history is unavailable</h2>
        <p className="mt-2 text-sm leading-6 text-slate-400">{message}</p>
        <button type="button" onClick={onRetry} className="secondary-button mt-6">
          <RefreshCcw aria-hidden="true" size={16} /> Retry
        </button>
      </div>
    </section>
  )
}

export default function HistoryPage() {
  const [records, setRecords] = useState([])
  const [status, setStatus] = useState('loading')
  const [loadError, setLoadError] = useState('')
  const [operationError, setOperationError] = useState('')
  const [feedback, setFeedback] = useState('')
  const [deletingId, setDeletingId] = useState(null)
  const [isClearing, setIsClearing] = useState(false)
  const [confirmingClear, setConfirmingClear] = useState(false)
  const loadControllerRef = useRef(null)
  const operationControllerRef = useRef(null)
  const confirmClearRef = useRef(null)

  const loadHistory = useCallback(async () => {
    loadControllerRef.current?.abort()
    const controller = new AbortController()
    loadControllerRef.current = controller
    setStatus('loading')
    setLoadError('')

    try {
      const history = await fetchPredictionHistory({ signal: controller.signal })
      if (controller.signal.aborted) return
      setRecords(history)
      setStatus('success')
    } catch (error) {
      if (error?.name === 'AbortError') return
      setLoadError(error instanceof Error ? error.message : 'Prediction history could not be loaded.')
      setStatus('error')
    } finally {
      if (loadControllerRef.current === controller) loadControllerRef.current = null
    }
  }, [])

  useEffect(() => {
    loadHistory()
    return () => {
      loadControllerRef.current?.abort()
      operationControllerRef.current?.abort()
    }
  }, [loadHistory])

  useEffect(() => {
    if (confirmingClear) confirmClearRef.current?.focus()
  }, [confirmingClear])

  const operationInProgress = deletingId !== null || isClearing

  const handleDelete = async (record) => {
    if (operationControllerRef.current || confirmingClear) return
    const controller = new AbortController()
    operationControllerRef.current = controller
    setDeletingId(record.id)
    setOperationError('')
    setFeedback('')

    try {
      await deletePredictionHistory(record.id, { signal: controller.signal })
      if (controller.signal.aborted) return
      setRecords((current) => current.filter(({ id }) => id !== record.id))
      setFeedback(`${record.location} prediction removed from history.`)
    } catch (error) {
      if (error?.name === 'AbortError') return
      setOperationError(error instanceof Error ? error.message : 'The prediction could not be deleted.')
    } finally {
      if (operationControllerRef.current === controller) operationControllerRef.current = null
      setDeletingId(null)
    }
  }

  const handleClearAll = async () => {
    if (operationControllerRef.current) return
    const controller = new AbortController()
    operationControllerRef.current = controller
    setIsClearing(true)
    setOperationError('')
    setFeedback('')

    try {
      const result = await clearPredictionHistory({ signal: controller.signal })
      if (controller.signal.aborted) return
      setRecords([])
      setConfirmingClear(false)
      setFeedback(`${result.deletedCount} ${result.deletedCount === 1 ? 'prediction' : 'predictions'} cleared.`)
    } catch (error) {
      if (error?.name === 'AbortError') return
      setOperationError(error instanceof Error ? error.message : 'Prediction history could not be cleared.')
    } finally {
      if (operationControllerRef.current === controller) operationControllerRef.current = null
      setIsClearing(false)
    }
  }

  return (
    <div className="page-container">
      <SectionHeader
        eyebrow="Prediction history"
        title="Your recent weather outlooks."
        description="Successful RainWise predictions are saved automatically and synchronized through the prediction service. Full weather-input forms are not retained."
      />

      {operationError && (
        <p role="alert" className="mt-6 rounded-xl border border-rose-300/20 bg-rose-300/[0.06] px-4 py-3 text-sm text-rose-200">
          {operationError}
        </p>
      )}
      {feedback && (
        <div className="mt-6 flex items-center gap-2 text-sm text-emerald-200" role="status">
          <CheckCircle2 aria-hidden="true" size={17} /> {feedback}
        </div>
      )}

      {status === 'loading' && <LoadingHistory />}
      {status === 'error' && <HistoryError message={loadError} onRetry={loadHistory} />}
      {status === 'success' && records.length === 0 && <EmptyHistory />}

      {status === 'success' && records.length > 0 && (
        <section className="mt-10" aria-labelledby="saved-history-heading" aria-busy={operationInProgress}>
          <div className="flex flex-col gap-4 border-b border-white/10 pb-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 id="saved-history-heading" className="text-xl font-extrabold text-white">Saved outlooks</h2>
              <p className="mt-1 text-sm text-slate-400">
                {records.length} {records.length === 1 ? 'record' : 'records'}, newest first
              </p>
            </div>
            <button
              type="button"
              onClick={() => setConfirmingClear(true)}
              disabled={operationInProgress || confirmingClear}
              className="secondary-button self-start sm:self-auto"
            >
              <ListRestart aria-hidden="true" size={17} /> Clear history
            </button>
          </div>

          {confirmingClear && (
            <div className="mt-5 flex flex-col gap-4 rounded-2xl border border-amber-300/20 bg-amber-300/[0.065] p-5 sm:flex-row sm:items-center sm:justify-between" role="alert">
              <div>
                <p className="text-sm font-extrabold text-white">Clear all prediction history?</p>
                <p className="mt-1 text-xs leading-5 text-amber-100/70">This permanently removes every saved outlook and cannot be undone.</p>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setConfirmingClear(false)}
                  disabled={isClearing}
                  className="secondary-button min-h-10 px-4 py-2 text-xs"
                >
                  <X aria-hidden="true" size={15} /> Cancel
                </button>
                <button
                  ref={confirmClearRef}
                  type="button"
                  onClick={handleClearAll}
                  disabled={operationInProgress}
                  className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl border border-rose-300/25 bg-rose-300/10 px-4 py-2 text-xs font-extrabold text-rose-100 transition hover:bg-rose-300/15 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300 disabled:pointer-events-none disabled:opacity-45"
                >
                  {isClearing ? <LoaderCircle aria-hidden="true" className="animate-spin" size={15} /> : <Trash2 aria-hidden="true" size={15} />}
                  {isClearing ? 'Clearing' : 'Confirm clear'}
                </button>
              </div>
            </div>
          )}

          <motion.ul
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 grid gap-4"
          >
            {records.map((record) => {
              const rainLikely = record.prediction === 'Yes'
              const riskLevel = getDisplayRiskLevel(record.rainProbability)
              const OutcomeIcon = rainLikely ? CloudRain : CloudSun
              const deleting = deletingId === record.id

              return (
                <li key={record.id}>
                  <article className="glass-panel rounded-2xl p-5 sm:p-6">
                    <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
                      <div className="flex min-w-0 items-start gap-4">
                        <span className={`grid size-12 shrink-0 place-items-center rounded-xl ${rainLikely ? 'bg-sky-300/12 text-sky-200' : 'bg-emerald-300/12 text-emerald-200'}`}>
                          <OutcomeIcon aria-hidden="true" size={23} />
                        </span>
                        <div className="min-w-0">
                          <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">{rainLikely ? 'Rain Likely' : 'Rain Unlikely'}</p>
                          <h3 className="mt-1 break-words text-xl font-extrabold text-white">{record.location}</h3>
                          <p className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-slate-400">
                            <Clock3 aria-hidden="true" size={13} /> Created {formatCreatedAt(record.createdAt)}
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDelete(record)}
                        disabled={operationInProgress || confirmingClear}
                        className="inline-flex min-h-10 items-center justify-center gap-2 self-start rounded-xl border border-white/10 px-3.5 py-2 text-xs font-bold text-slate-400 transition hover:border-rose-300/25 hover:bg-rose-300/[0.07] hover:text-rose-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300 disabled:pointer-events-none disabled:opacity-40 sm:self-auto"
                        aria-label={`Delete ${record.location} prediction from ${record.observationDate}`}
                      >
                        {deleting ? <LoaderCircle aria-hidden="true" className="animate-spin" size={16} /> : <Trash2 aria-hidden="true" size={16} />}
                        {deleting ? 'Deleting' : 'Delete'}
                      </button>
                    </div>

                    <dl className="mt-5 grid gap-4 border-t border-white/[0.07] pt-5 sm:grid-cols-3">
                      <div>
                        <dt className="text-[0.68rem] font-bold uppercase tracking-[0.12em] text-slate-400">Observation date</dt>
                        <dd className="mt-1.5 text-sm font-bold text-slate-200">{formatObservationDate(record.observationDate)}</dd>
                      </div>
                      <div>
                        <dt className="text-[0.68rem] font-bold uppercase tracking-[0.12em] text-slate-400">Rain probability</dt>
                        <dd className="mt-1.5 text-lg font-extrabold text-white">{formatProbability(record.rainProbability)}%</dd>
                      </div>
                      <div>
                        <dt className="text-[0.68rem] font-bold uppercase tracking-[0.12em] text-slate-400">Display risk</dt>
                        <dd className="mt-1.5">
                          <span className={`inline-flex rounded-lg border px-2.5 py-1 text-xs font-extrabold ${riskStyles[riskLevel]}`}>
                            {riskLevel}
                          </span>
                        </dd>
                      </div>
                    </dl>
                  </article>
                </li>
              )
            })}
          </motion.ul>

        </section>
      )}
    </div>
  )
}
