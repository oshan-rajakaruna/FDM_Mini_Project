import { motion } from 'framer-motion'

const drops = [10, 22, 38, 53, 68, 82, 93]

export default function WeatherBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden="true">
      <div className="atmosphere-grid absolute inset-0 opacity-45" />
      <motion.div
        className="absolute -right-40 -top-52 size-[38rem] rounded-full bg-sky-400/[0.08] blur-3xl"
        animate={{ x: [0, -35, 0], y: [0, 28, 0] }}
        transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="absolute -bottom-72 left-[12%] size-[34rem] rounded-full bg-cyan-300/[0.055] blur-3xl"
        animate={{ x: [0, 45, 0], y: [0, -24, 0] }}
        transition={{ duration: 22, repeat: Infinity, ease: 'easeInOut' }}
      />
      <div className="absolute right-[8%] top-[12%] hidden h-36 w-28 opacity-20 lg:block">
        {drops.map((left, index) => (
          <span
            key={left}
            className="rain-line"
            style={{ left: `${left}%`, animationDelay: `${index * 0.27}s` }}
          />
        ))}
      </div>
    </div>
  )
}

