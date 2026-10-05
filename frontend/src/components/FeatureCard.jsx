import { motion } from 'framer-motion'
import { ArrowUpRight } from 'lucide-react'

export default function FeatureCard({ icon: Icon, title, description, index = 0 }) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.25 }}
      transition={{ delay: index * 0.07, duration: 0.45 }}
      className="glass-panel group rounded-2xl p-5 transition duration-300 hover:-translate-y-1 hover:border-cyan-200/20 hover:bg-white/[0.085] sm:p-6"
    >
      <div className="flex items-start justify-between">
        <span className="grid size-11 place-items-center rounded-xl border border-sky-300/15 bg-sky-300/10 text-cyan-200">
          <Icon aria-hidden="true" size={22} strokeWidth={1.8} />
        </span>
        <ArrowUpRight
          aria-hidden="true"
          className="text-slate-600 transition group-hover:text-cyan-200"
          size={18}
        />
      </div>
      <h3 className="mt-8 text-lg font-bold tracking-tight text-white">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
    </motion.article>
  )
}

