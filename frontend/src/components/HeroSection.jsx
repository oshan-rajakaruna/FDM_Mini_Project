import { motion } from 'framer-motion'
import { ArrowRight, CloudRain, Droplets, Sparkles, Wind } from 'lucide-react'
import { Link } from 'react-router-dom'

const rainDrops = [14, 27, 41, 56, 70, 84]

function WeatherVisual() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.94 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.75, delay: 0.15 }}
      className="relative mx-auto aspect-square w-full max-w-[31rem]"
      aria-hidden="true"
    >
      <motion.div
        className="weather-orbit absolute inset-[7%] rounded-full border border-sky-200/10 bg-sky-300/[0.035]"
        animate={{ rotate: 360 }}
        transition={{ duration: 70, repeat: Infinity, ease: 'linear' }}
      >
        <span className="absolute left-1/2 top-[-5px] size-2 -translate-x-1/2 rounded-full bg-cyan-200 shadow-[0_0_18px_#72e3ef]" />
      </motion.div>
      <div className="absolute inset-[18%] rounded-full border border-white/10 bg-gradient-to-br from-sky-300/15 via-slate-900/30 to-cyan-300/5 shadow-[inset_0_0_60px_rgba(96,211,255,0.08)] backdrop-blur-sm" />
      <motion.div
        className="absolute left-[18%] top-[24%] flex h-[30%] w-[62%] items-center justify-center rounded-[50%] border border-white/15 bg-slate-100/90 text-slate-700 shadow-[0_28px_60px_rgba(0,7,19,0.4)]"
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 5.8, repeat: Infinity, ease: 'easeInOut' }}
      >
        <CloudRain size={82} strokeWidth={1.15} />
      </motion.div>
      <div className="absolute left-[24%] top-[54%] h-[26%] w-[52%] overflow-hidden">
        {rainDrops.map((left, index) => (
          <span
            key={left}
            className="rain-line"
            style={{ left: `${left}%`, animationDelay: `${index * 0.34}s` }}
          />
        ))}
      </div>
      <motion.div
        className="glass-panel absolute bottom-[10%] left-[2%] rounded-2xl px-4 py-3"
        animate={{ y: [0, 6, 0] }}
        transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
      >
        <div className="flex items-center gap-2 text-xs font-bold text-cyan-100">
          <Droplets size={16} /> Rain-aware planning
        </div>
      </motion.div>
      <motion.div
        className="glass-panel absolute right-[1%] top-[12%] rounded-2xl px-4 py-3"
        animate={{ y: [0, -7, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
      >
        <div className="flex items-center gap-2 text-xs font-bold text-sky-100">
          <Wind size={16} /> Weather signals
        </div>
      </motion.div>
    </motion.div>
  )
}

export default function HeroSection() {
  return (
    <section className="hero-sheen glass-panel relative overflow-hidden rounded-[2rem] px-6 py-10 sm:px-9 sm:py-14 lg:px-12 lg:py-16">
      <div className="absolute left-0 top-0 h-px w-full bg-gradient-to-r from-transparent via-cyan-200/60 to-transparent" />
      <div className="relative z-10 grid items-center gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-3xl"
        >
          <div className="eyebrow">
            <Sparkles aria-hidden="true" size={15} />
            AI-powered weather intelligence
          </div>
          <h1 className="mt-5 text-[clamp(2.65rem,6vw,5.4rem)] font-extrabold leading-[0.96] tracking-[-0.065em] text-white">
            Know Tomorrow.
            <span className="mt-2 block text-transparent bg-clip-text bg-gradient-to-r from-sky-300 to-cyan-200">
              Plan Today.
            </span>
          </h1>
          <p className="mt-7 max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">
            RainWise turns today&apos;s weather observations into a clear next-day rainfall
            outlook, helping people make practical plans with greater confidence.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link to="/predict" className="primary-button">
              Predict Tomorrow&apos;s Rain
              <ArrowRight aria-hidden="true" size={18} />
            </Link>
            <a href="#how-it-works" className="secondary-button">
              Learn How It Works
            </a>
          </div>
          <div className="mt-9 flex flex-wrap gap-x-7 gap-y-3 border-t border-white/10 pt-6 text-xs font-semibold text-slate-400">
            <span className="flex items-center gap-2">
              <span className="size-1.5 rounded-full bg-cyan-300" /> Next-day outlook
            </span>
            <span className="flex items-center gap-2">
              <span className="size-1.5 rounded-full bg-sky-400" /> Decision support
            </span>
            <span className="flex items-center gap-2">
              <span className="size-1.5 rounded-full bg-indigo-300" /> Australian weather data
            </span>
          </div>
        </motion.div>
        <WeatherVisual />
      </div>
    </section>
  )
}

