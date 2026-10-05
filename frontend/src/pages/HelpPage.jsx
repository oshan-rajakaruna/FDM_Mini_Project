import { CloudSun, Droplets, Gauge, Search, Sun, Thermometer, Wind } from 'lucide-react'
import { motion } from 'framer-motion'
import SectionHeader from '../components/SectionHeader'

const categories = [
  { icon: Thermometer, title: 'Temperature', hint: 'Daily minimums, maximums, and temperature changes.' },
  { icon: Droplets, title: 'Rain', hint: 'Rainfall observations and current rain conditions.' },
  { icon: Droplets, title: 'Humidity', hint: 'Morning and afternoon moisture levels in the air.' },
  { icon: Gauge, title: 'Pressure', hint: 'Atmospheric pressure readings across the day.' },
  { icon: Wind, title: 'Wind', hint: 'Direction, gusts, and morning or afternoon wind speed.' },
  { icon: CloudSun, title: 'Cloud / Sunshine', hint: 'Sky cover and available sunshine observations.' },
]

export default function HelpPage() {
  return (
    <div className="page-container">
      <SectionHeader
        eyebrow="Help & field guide"
        title="Understand every weather input."
        description="The field guide will explain what RainWise asks for, where to find each observation, and why it helps describe the day’s weather."
      />

      <div className="glass-panel mt-10 rounded-[1.5rem] p-4 sm:p-5">
        <label htmlFor="field-search" className="sr-only">Search weather fields</label>
        <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-slate-950/30 px-4 py-3.5 focus-within:border-cyan-300/40 focus-within:ring-2 focus-within:ring-cyan-300/10">
          <Search aria-hidden="true" className="shrink-0 text-slate-500" size={20} />
          <input
            id="field-search"
            type="search"
            placeholder="Search weather fields..."
            className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-600"
          />
          <span className="hidden rounded-lg border border-white/10 px-2 py-1 text-[0.65rem] font-bold uppercase tracking-wider text-slate-500 sm:inline">Coming soon</span>
        </div>
      </div>

      <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-label="Weather field categories">
        {categories.map(({ icon: Icon, title, hint }, index) => (
          <motion.article
            key={title}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.055 }}
            className="glass-panel group min-h-52 rounded-2xl p-6 transition hover:border-sky-300/20 hover:bg-white/[0.08]"
          >
            <span className="grid size-12 place-items-center rounded-2xl border border-sky-200/10 bg-sky-300/10 text-cyan-200 transition group-hover:scale-105">
              <Icon aria-hidden="true" size={23} strokeWidth={1.8} />
            </span>
            <h2 className="mt-7 text-lg font-bold text-white">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{hint}</p>
          </motion.article>
        ))}
      </section>

      <aside className="mt-8 flex flex-col gap-4 rounded-2xl border border-indigo-300/15 bg-indigo-300/[0.055] p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-xl bg-indigo-300/10 text-indigo-200">
            <Sun size={20} />
          </span>
          <div>
            <p className="text-sm font-bold text-white">Field definitions are coming next.</p>
            <p className="mt-1 text-xs leading-5 text-slate-400">This page currently establishes the visual guide and category structure.</p>
          </div>
        </div>
      </aside>
    </div>
  )
}

