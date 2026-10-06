import { AnimatePresence, motion } from 'framer-motion'
import { Cable, CheckCircle2, History, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import OutcomeSummary from './OutcomeSummary'
import ResultErrorState from './ResultErrorState'
import ResultLoadingState from './ResultLoadingState'
import WeatherInputSummary from './WeatherInputSummary'

function ReadyState() {
  return (
    <div className="glass-panel rounded-[1.5rem] p-7 text-center sm:p-10">
      <span className="mx-auto grid size-14 place-items-center rounded-2xl border border-white/10 bg-white/[0.045] text-slate-400">
        <Cable aria-hidden="true" size={24} />
      </span>
      <h3 className="mt-5 text-lg font-extrabold text-white">Ready for your weather observations</h3>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-400">
        Review the form and submit it to generate an outlook from the saved RainWise model.
      </p>
    </div>
  )
}

export default function PredictionResultSection({
  status,
  result,
  error,
  onClearError,
  values,
}) {
  return (
    <section id="prediction-result" className="mt-8 scroll-mt-6" aria-labelledby="prediction-result-heading">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <span className="eyebrow"><Sparkles aria-hidden="true" size={15} /> Result experience</span>
          <h2 id="prediction-result-heading" className="mt-3 text-2xl font-extrabold tracking-tight text-white sm:text-3xl">
            Tomorrow&apos;s rainfall outlook
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
            Model output, probability context, and practical decision-support guidance.
          </p>
        </div>
      </header>

      <div className="mt-5" aria-live="polite">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={status}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
          >
            {status === 'idle' && <ReadyState />}
            {status === 'loading' && <ResultLoadingState />}
            {status === 'error' && (
              <ResultErrorState message={error} onReset={onClearError} />
            )}
            {status === 'success' && result && (
              <div className="space-y-5">
                <OutcomeSummary result={result} />
                <div className="flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/[0.035] p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 aria-hidden="true" className="mt-0.5 shrink-0 text-emerald-200" size={20} />
                    <div>
                      <p className="text-sm font-bold text-white">Added to Prediction History</p>
                      <p className="mt-1 text-xs leading-5 text-slate-400">
                        The successful outlook is available across sessions through the RainWise service.
                      </p>
                    </div>
                  </div>
                  <Link to="/history" className="secondary-button shrink-0">
                    <History aria-hidden="true" size={16} /> View history
                  </Link>
                </div>
                <WeatherInputSummary values={values} />
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  )
}
