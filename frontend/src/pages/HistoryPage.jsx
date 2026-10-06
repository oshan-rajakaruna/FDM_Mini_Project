import { motion } from 'framer-motion'
import {
  ArrowRight,
  Clock3,
  CloudRain,
  CloudSun,
  ListRestart,
  Trash2,
} from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import SectionHeader from '../components/SectionHeader'
import {
  clearPredictionHistory,
  deletePredictionHistory,
  loadPredictionHistory,
} from '../utils/historyStorage'

const riskStyles = {
  Low: 'border-emerald-300/20 bg-emerald-300/10 text-emerald-100',
  Moderate: 'border-amber-300/20 bg-amber-300/10 text-amber-100',
  High: 'border-rose-300/20 bg-rose-300/10 text-rose-100',
}

function formatSavedAt(value) {
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

function EmptyHistory() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel relative mt-10 grid min-h-[31rem] place-items-center overflow-hidden rounded-[2rem] p-7 text-center"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(66,190,255,0.08),transparent_42%)]" />
      <div className="relative max-w-md">
        <div className="relative mx-auto grid size-24 place-items-center rounded-[2rem] border border-sky-200/15 bg-sky-300/10 text-cyan-200">
          <Clock3 aria-hidden="true" size={39} strokeWidth={1.5} />
          <span className="absolute -bottom-2 -right-2 grid size-10 place-items-center rounded-xl border-4 border-[#0b1b30] bg-slate-100 text-slate-700">
            <CloudRain aria-hidden="true" size={19} />
          </span>
        </div>
        <h2 className="mt-9 text-2xl font-extrabold tracking-tight text-white">No saved predictions yet.</h2>
        <p className="mt-3 text-sm leading-7 text-slate-400">
          Generate a real prediction, then choose Save to history to keep a compact record on this device.
        </p>
        <Link to="/predict" className="secondary-button mt-7">
          Visit prediction workspace <ArrowRight aria-hidden="true" size={17} />
        </Link>
      </div>
    </motion.section>
  )
}

export default function HistoryPage() {
  const [records, setRecords] = useState(() => loadPredictionHistory())
  const [storageError, setStorageError] = useState('')

  const handleDelete = (id) => {
    try {
      setRecords(deletePredictionHistory(id))
      setStorageError('')
    } catch (error) {
      setStorageError(error instanceof Error ? error.message : 'The history record could not be deleted.')
    }
  }

  const handleClearAll = () => {
    if (!window.confirm('Clear all saved RainWise prediction history from this device?')) return
    try {
      clearPredictionHistory()
      setRecords([])
      setStorageError('')
    } catch (error) {
      setStorageError(error instanceof Error ? error.message : 'Prediction history could not be cleared.')
    }
  }

  return (
    <div className="page-container">
      <SectionHeader
        eyebrow="Prediction history"
        title="Your recent weather outlooks."
        description="Predictions you choose to save stay in this browser on this device. Full weather-input forms are not retained."
      />

      {storageError && (
        <p role="alert" className="mt-6 rounded-xl border border-rose-300/20 bg-rose-300/[0.06] px-4 py-3 text-sm text-rose-200">
          {storageError}
        </p>
      )}

      {records.length === 0 ? (
        <EmptyHistory />
      ) : (
        <section className="mt-10" aria-labelledby="saved-history-heading">
          <div className="flex flex-col gap-4 border-b border-white/10 pb-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 id="saved-history-heading" className="text-xl font-extrabold text-white">
                Saved outlooks
              </h2>
              <p className="mt-1 text-sm text-slate-400">
                {records.length} {records.length === 1 ? 'record' : 'records'}, newest first
              </p>
            </div>
            <button type="button" onClick={handleClearAll} className="secondary-button self-start sm:self-auto">
              <ListRestart aria-hidden="true" size={17} /> Clear all
            </button>
          </div>

          <motion.ul
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 grid gap-4"
          >
            {records.map((record) => {
              const rainLikely = record.prediction === 'Yes'
              const OutcomeIcon = rainLikely ? CloudRain : CloudSun
              return (
                <li key={record.id}>
                  <article className="glass-panel rounded-2xl p-5 sm:p-6">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex min-w-0 items-start gap-4">
                        <span className={`grid size-11 shrink-0 place-items-center rounded-xl ${rainLikely ? 'bg-sky-300/12 text-sky-200' : 'bg-emerald-300/12 text-emerald-200'}`}>
                          <OutcomeIcon aria-hidden="true" size={22} />
                        </span>
                        <div className="min-w-0">
                          <h3 className="truncate text-lg font-extrabold text-white">{record.location}</h3>
                          <p className="mt-1 text-sm font-semibold text-slate-300">
                            {rainLikely ? 'Rain Likely' : 'Rain Unlikely'}
                          </p>
                          <p className="mt-2 flex items-center gap-1.5 text-xs text-slate-500">
                            <Clock3 aria-hidden="true" size={13} /> Saved {formatSavedAt(record.savedAt)}
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDelete(record.id)}
                        className="grid size-10 shrink-0 place-items-center rounded-xl border border-white/10 text-slate-400 transition hover:border-rose-300/25 hover:bg-rose-300/[0.07] hover:text-rose-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300"
                        aria-label={`Delete ${record.location} prediction from ${record.observationDate}`}
                      >
                        <Trash2 aria-hidden="true" size={17} />
                      </button>
                    </div>

                    <dl className="mt-5 grid gap-3 border-t border-white/[0.07] pt-4 sm:grid-cols-3">
                      <div>
                        <dt className="text-[0.68rem] font-bold uppercase tracking-[0.12em] text-slate-500">Observation date</dt>
                        <dd className="mt-1 text-sm font-bold text-slate-200">{formatObservationDate(record.observationDate)}</dd>
                      </div>
                      <div>
                        <dt className="text-[0.68rem] font-bold uppercase tracking-[0.12em] text-slate-500">Rain probability</dt>
                        <dd className="mt-1 text-sm font-bold text-slate-200">{Math.round(record.rainProbability * 1000) / 10}%</dd>
                      </div>
                      <div>
                        <dt className="text-[0.68rem] font-bold uppercase tracking-[0.12em] text-slate-500">Display risk</dt>
                        <dd className="mt-1">
                          <span className={`inline-flex rounded-lg border px-2.5 py-1 text-xs font-extrabold ${riskStyles[record.riskLevel]}`}>
                            {record.riskLevel}
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
