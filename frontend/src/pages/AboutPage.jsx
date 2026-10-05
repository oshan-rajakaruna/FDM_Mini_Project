import { Binary, BrainCircuit, CloudSun, Database, Goal, ShieldCheck } from 'lucide-react'
import { motion } from 'framer-motion'
import SectionHeader from '../components/SectionHeader'

const sections = [
  {
    icon: Goal,
    title: 'Project Goal',
    text: 'RainWise is designed to support next-day rainfall awareness and practical weather-risk decisions through a focused, understandable digital experience.',
  },
  {
    icon: BrainCircuit,
    title: 'Machine Learning Approach',
    text: 'The project prepares weather observations for supervised binary classification, comparing candidate approaches before selecting a final model.',
  },
  {
    icon: Database,
    title: 'Dataset Overview',
    text: 'The modeling work uses Australian weather observations that combine location, date, temperature, rainfall, wind, humidity, pressure, cloud, and sunshine information.',
  },
  {
    icon: CloudSun,
    title: 'Final Model',
    text: 'The selected final model is a Random Forest. It produces a binary outlook for the RainTomorrow target: Rain or No Rain.',
  },
  {
    icon: ShieldCheck,
    title: 'Decision Support Purpose',
    text: 'The prediction is intended to add useful planning context. It supports human decisions rather than replacing official forecasts or professional advice.',
  },
]

export default function AboutPage() {
  return (
    <div className="page-container">
      <SectionHeader
        eyebrow="About RainWise"
        title="A clearer view of tomorrow."
        description="RainWise brings the project’s rainfall-prediction work into a calm, approachable interface centered on responsible decision support."
      />

      <div className="mt-10 grid gap-5 lg:grid-cols-[0.72fr_1.28fr]">
        <aside className="relative overflow-hidden rounded-[1.75rem] border border-cyan-200/15 bg-cyan-300/[0.07] p-7 sm:p-9">
          <div className="absolute -right-16 -top-16 size-56 rounded-full bg-sky-300/10 blur-3xl" />
          <span className="relative grid size-14 place-items-center rounded-2xl border border-white/10 bg-white/[0.08] text-cyan-200">
            <Binary size={27} />
          </span>
          <p className="relative mt-16 text-xs font-bold uppercase tracking-[0.18em] text-cyan-200/70">Prediction target</p>
          <h2 className="relative mt-3 text-3xl font-extrabold tracking-tight text-white">RainTomorrow</h2>
          <p className="relative mt-4 text-sm leading-7 text-slate-300">
            A binary next-day outcome built from current and recent weather observations.
          </p>
          <dl className="relative mt-10 space-y-4 border-t border-white/10 pt-6 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-slate-400">Final model</dt>
              <dd className="font-bold text-white">Random Forest</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-400">Output</dt>
              <dd className="font-bold text-white">Rain / No Rain</dd>
            </div>
          </dl>
        </aside>

        <section className="space-y-4" aria-label="Project information">
          {sections.map(({ icon: Icon, title, text }, index) => (
            <motion.article
              key={title}
              initial={{ opacity: 0, x: 15 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.055 }}
              className="glass-panel flex gap-4 rounded-2xl p-5 sm:gap-5 sm:p-6"
            >
              <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-sky-300/10 text-cyan-200">
                <Icon aria-hidden="true" size={21} strokeWidth={1.8} />
              </span>
              <div>
                <h2 className="text-base font-bold text-white">{title}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
              </div>
            </motion.article>
          ))}
        </section>
      </div>
    </div>
  )
}

