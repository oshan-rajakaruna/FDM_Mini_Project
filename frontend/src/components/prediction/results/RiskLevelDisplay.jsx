const RISK_LEVELS = ['Low', 'Moderate', 'High']

const activeStyles = {
  Low: 'border-emerald-300/30 bg-emerald-300/12 text-emerald-100',
  Moderate: 'border-amber-300/30 bg-amber-300/12 text-amber-100',
  High: 'border-rose-300/30 bg-rose-300/12 text-rose-100',
}

export default function RiskLevelDisplay({ level }) {
  return (
    <section aria-labelledby="risk-level-heading">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h4 id="risk-level-heading" className="text-sm font-bold text-white">Display risk level</h4>
        <span className="text-xs font-semibold text-slate-500">Current: {level}</span>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2" aria-label={`Risk level: ${level}`}>
        {RISK_LEVELS.map((riskLevel) => {
          const active = riskLevel === level
          return (
            <span
              key={riskLevel}
              className={`rounded-lg border px-2 py-2 text-center text-[0.68rem] font-extrabold uppercase tracking-[0.1em] ${
                active ? activeStyles[riskLevel] : 'border-white/[0.07] bg-white/[0.025] text-slate-600'
              }`}
              aria-current={active ? 'true' : undefined}
            >
              {riskLevel}
            </span>
          )
        })}
      </div>
      <p className="mt-3 text-[0.68rem] leading-5 text-slate-500">
        Low, Moderate, and High are display-only guidance bands—not model thresholds.
      </p>
    </section>
  )
}
