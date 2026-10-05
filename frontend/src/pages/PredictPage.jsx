import { Check, CloudSun, MapPin, Wind } from 'lucide-react'
import { motion } from 'framer-motion'
import SectionHeader from '../components/SectionHeader'

const steps = [
  { number: '01', title: 'Location', icon: MapPin, description: 'Choose the observation location.' },
  { number: '02', title: 'Weather', icon: CloudSun, description: 'Add core weather measurements.' },
  { number: '03', title: 'Wind & Atmosphere', icon: Wind, description: 'Complete atmospheric conditions.' },
  { number: '04', title: 'Review & Predict', icon: Check, description: 'Review inputs before prediction.' },
]

export default function PredictPage() {
  return (
    <div className="page-container">
      <SectionHeader
        eyebrow="Prediction workspace"
        title="Build tomorrow’s rainfall outlook."
        description="The guided prediction workflow is being prepared. This foundation shows the journey without collecting data or calling a prediction service yet."
      />

      <ol className="mt-10 grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Prediction steps">
        {steps.map(({ number, title }, index) => (
          <li
            key={title}
            className={`relative rounded-2xl border p-4 ${
              index === 0
                ? 'border-cyan-300/25 bg-cyan-300/10'
                : 'border-white/10 bg-white/[0.035]'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className={`grid size-8 place-items-center rounded-lg text-xs font-extrabold ${index === 0 ? 'bg-cyan-300 text-slate-950' : 'bg-white/10 text-slate-400'}`}>
                {number}
              </span>
              <span className={`text-sm font-bold ${index === 0 ? 'text-white' : 'text-slate-400'}`}>
                {title}
              </span>
            </div>
            {index < steps.length - 1 && (
              <span className="absolute -right-2 top-1/2 z-10 hidden h-px w-4 bg-white/15 xl:block" />
            )}
          </li>
        ))}
      </ol>

      <section className="mt-8 grid gap-5 lg:grid-cols-2">
        {steps.map(({ number, title, icon: Icon, description }, index) => (
          <motion.article
            key={title}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.06 }}
            className="glass-panel min-h-64 rounded-[1.5rem] p-6 sm:p-7"
          >
            <div className="flex items-start justify-between gap-4">
              <span className="grid size-12 place-items-center rounded-2xl border border-sky-300/15 bg-sky-300/10 text-cyan-200">
                <Icon aria-hidden="true" size={23} strokeWidth={1.8} />
              </span>
              <span className="text-xs font-extrabold tracking-[0.2em] text-slate-600">{number}</span>
            </div>
            <h2 className="mt-7 text-xl font-bold text-white">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
            <div className="mt-7 rounded-xl border border-dashed border-white/15 bg-slate-950/20 px-4 py-5 text-center text-xs font-semibold text-slate-500">
              Input controls will be added in the next implementation stage.
            </div>
          </motion.article>
        ))}
      </section>

      <div className="mt-6 flex items-center justify-between rounded-2xl border border-amber-300/15 bg-amber-300/[0.055] px-5 py-4 text-sm text-amber-100/80">
        <span>No prediction API is connected in this frontend foundation.</span>
        <span className="hidden rounded-full bg-amber-300/10 px-3 py-1 text-xs font-bold sm:inline">Preview only</span>
      </div>
    </div>
  )
}

