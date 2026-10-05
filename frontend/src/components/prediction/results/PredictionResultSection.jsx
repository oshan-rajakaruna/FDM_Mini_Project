import { AnimatePresence, motion } from 'framer-motion'
import { Beaker, Cable, Sparkles } from 'lucide-react'
import { DEMO_RESULT_PREVIEWS, RESULT_PREVIEW_STATES } from '../../../data/resultPreviewData'
import OutcomeSummary from './OutcomeSummary'
import ResultErrorState from './ResultErrorState'
import ResultLoadingState from './ResultLoadingState'
import WeatherInputSummary from './WeatherInputSummary'

function ReadyState({ previewEnabled }) {
  return (
    <div className="glass-panel rounded-[1.5rem] p-7 text-center sm:p-10">
      <span className="mx-auto grid size-14 place-items-center rounded-2xl border border-white/10 bg-white/[0.045] text-slate-400">
        <Cable aria-hidden="true" size={24} />
      </span>
      <h3 className="mt-5 text-lg font-extrabold text-white">Awaiting prediction integration</h3>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-400">
        No prediction has been generated. This result area is ready for a future backend response without making a request today.
      </p>
      {previewEnabled && (
        <p className="mt-4 text-xs font-semibold text-amber-200/80">
          Choose a demo state above to inspect the result interface.
        </p>
      )}
    </div>
  )
}

export default function PredictionResultSection({ previewState, onPreviewStateChange, previewEnabled, values }) {
  const previewResult = DEMO_RESULT_PREVIEWS[previewState]

  return (
    <section id="prediction-result" className="mt-8" aria-labelledby="prediction-result-heading">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <span className="eyebrow"><Sparkles aria-hidden="true" size={15} /> Result experience</span>
          <h2 id="prediction-result-heading" className="mt-3 text-2xl font-extrabold tracking-tight text-white sm:text-3xl">
            Tomorrow&apos;s rainfall outlook
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
            A responsive presentation area for the future prediction response and planning guidance.
          </p>
        </div>
      </header>

      {previewEnabled && (
        <div className="mt-5 rounded-2xl border border-amber-300/20 bg-amber-300/[0.065] p-4" aria-label="Result UI preview controls">
          <div className="flex items-start gap-3">
            <Beaker aria-hidden="true" className="mt-0.5 shrink-0 text-amber-200" size={18} />
            <div className="min-w-0 flex-1">
              <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-amber-200">UI preview only</p>
              <p className="mt-1 text-xs leading-5 text-amber-100/65">
                These controls display illustrative component states. They do not call an API or run the model.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {RESULT_PREVIEW_STATES.map((state) => (
                  <button
                    key={state.id}
                    type="button"
                    onClick={() => onPreviewStateChange(state.id)}
                    aria-pressed={previewState === state.id}
                    className={`min-h-9 rounded-lg border px-3 py-2 text-xs font-bold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-200 ${
                      previewState === state.id
                        ? 'border-amber-200/40 bg-amber-200/15 text-amber-50'
                        : 'border-white/10 bg-white/[0.04] text-slate-300 hover:border-white/20 hover:bg-white/[0.08]'
                    }`}
                  >
                    {state.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="mt-5" aria-live="polite">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={previewEnabled ? previewState : 'idle'}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
          >
            {(!previewEnabled || previewState === 'idle') && <ReadyState previewEnabled={previewEnabled} />}
            {previewEnabled && previewState === 'loading' && <ResultLoadingState />}
            {previewEnabled && previewState === 'error' && (
              <ResultErrorState onReset={() => onPreviewStateChange('idle')} />
            )}
            {previewEnabled && previewResult && (
              <div className="space-y-5">
                <OutcomeSummary result={previewResult} />
                <WeatherInputSummary values={values} />
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  )
}
