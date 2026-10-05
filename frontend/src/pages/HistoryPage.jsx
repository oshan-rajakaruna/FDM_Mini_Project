import { ArrowRight, Clock3, CloudRain } from 'lucide-react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import SectionHeader from '../components/SectionHeader'

export default function HistoryPage() {
  return (
    <div className="page-container">
      <SectionHeader
        eyebrow="Prediction history"
        title="Your recent weather outlooks."
        description="Once prediction services are connected, this space will keep recent RainWise results organized and easy to revisit."
      />

      <motion.section
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel relative mt-10 grid min-h-[31rem] place-items-center overflow-hidden rounded-[2rem] p-7 text-center"
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(66,190,255,0.08),transparent_42%)]" />
        <div className="relative max-w-md">
          <div className="relative mx-auto grid size-24 place-items-center rounded-[2rem] border border-sky-200/15 bg-sky-300/10 text-cyan-200">
            <Clock3 size={39} strokeWidth={1.5} />
            <span className="absolute -bottom-2 -right-2 grid size-10 place-items-center rounded-xl border-4 border-[#0b1b30] bg-slate-100 text-slate-700">
              <CloudRain size={19} />
            </span>
          </div>
          <h2 className="mt-9 text-2xl font-extrabold tracking-tight text-white">No predictions yet.</h2>
          <p className="mt-3 text-sm leading-7 text-slate-400">
            Recent predictions will appear here later, giving you a simple view of previous locations, outcomes, and planning guidance.
          </p>
          <Link to="/predict" className="secondary-button mt-7">
            Visit prediction workspace <ArrowRight size={17} />
          </Link>
        </div>
      </motion.section>
    </div>
  )
}

