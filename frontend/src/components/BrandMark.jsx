import { CloudRainWind } from 'lucide-react'

export default function BrandMark({ compact = false }) {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <span className="grid size-11 shrink-0 place-items-center rounded-2xl border border-cyan-200/20 bg-cyan-300/10 text-cyan-200 shadow-[0_0_30px_rgba(65,195,255,0.16)]">
        <CloudRainWind aria-hidden="true" size={24} strokeWidth={1.8} />
      </span>
      {!compact && (
        <span className="min-w-0">
          <span className="block text-[1.08rem] font-extrabold tracking-tight text-white">
            RainWise
          </span>
          <span className="block truncate text-[0.63rem] font-bold uppercase tracking-[0.17em] text-sky-200/55">
            Weather intelligence
          </span>
        </span>
      )}
    </div>
  )
}

