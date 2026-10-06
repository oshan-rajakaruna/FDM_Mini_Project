import { motion } from 'framer-motion'

const SIZE = 152
const STROKE_WIDTH = 12
const RADIUS = (SIZE - STROKE_WIDTH) / 2
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

export default function ProbabilityGauge({ probability }) {
  const normalizedProbability = Math.min(100, Math.max(0, Number(probability) || 0))
  const offset = CIRCUMFERENCE * (1 - normalizedProbability / 100)

  return (
    <figure
      className="relative grid size-40 shrink-0 place-items-center"
      role="img"
      aria-label={`Rain probability: ${normalizedProbability} percent`}
    >
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="size-full -rotate-90" aria-hidden="true">
        <defs>
          <linearGradient id="rain-probability-gradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#72e3ef" />
            <stop offset="100%" stopColor="#49b9ff" />
          </linearGradient>
        </defs>
        <circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth={STROKE_WIDTH}
        />
        <motion.circle
          cx={SIZE / 2}
          cy={SIZE / 2}
          r={RADIUS}
          fill="none"
          stroke="url(#rain-probability-gradient)"
          strokeLinecap="round"
          strokeWidth={STROKE_WIDTH}
          strokeDasharray={CIRCUMFERENCE}
          initial={{ strokeDashoffset: CIRCUMFERENCE }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.75, ease: 'easeOut' }}
        />
      </svg>
      <figcaption className="absolute inset-0 grid place-content-center text-center">
        <span className="text-3xl font-extrabold tracking-[-0.05em] text-white">{normalizedProbability}%</span>
        <span className="mt-1 text-[0.62rem] font-extrabold uppercase tracking-[0.16em] text-slate-400">
          Rain probability
        </span>
      </figcaption>
    </figure>
  )
}
