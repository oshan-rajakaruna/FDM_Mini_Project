import { CircleAlert } from 'lucide-react'

export default function NumericField({
  name,
  label,
  value,
  error,
  onChange,
  unit,
  min,
  max,
  step = 0.1,
}) {
  const missing = value === null
  const errorId = `${name}-error`
  const hintId = `${name}-hint`

  return (
    <div>
      <div className="mb-2 flex min-h-5 items-center justify-between gap-3">
        <label htmlFor={name} className="text-sm font-bold text-slate-200">
          {label}
        </label>
        <span className="text-[0.62rem] font-bold uppercase tracking-[0.12em] text-slate-500">Optional</span>
      </div>
      <div className="relative">
        <input
          id={name}
          name={name}
          type="number"
          inputMode="decimal"
          min={min}
          max={max}
          step={step}
          value={missing ? '' : value}
          disabled={missing}
          onChange={(event) => onChange(name, event.target.value)}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${hintId} ${errorId}` : hintId}
          className={`field-control pr-16 ${error ? 'border-rose-300/60 focus:border-rose-300 focus:ring-rose-300/15' : ''}`}
        />
        <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-slate-500">
          {unit}
        </span>
      </div>
      <div className="mt-2 flex items-start justify-between gap-3">
        <p id={hintId} className="text-[0.68rem] leading-5 text-slate-500">
          Missing values are supported.
        </p>
        <label className="flex shrink-0 cursor-pointer items-center gap-2 text-[0.68rem] font-semibold text-slate-400 transition hover:text-slate-200">
          <input
            type="checkbox"
            checked={missing}
            onChange={(event) => onChange(name, event.target.checked ? null : '')}
            aria-label={`Mark ${label} as not available`}
            className="size-3.5 rounded border-white/20 bg-slate-950 text-cyan-300 accent-cyan-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300"
          />
          Not available
        </label>
      </div>
      {error && (
        <p id={errorId} role="alert" className="mt-2 flex items-start gap-1.5 text-xs leading-5 text-rose-300">
          <CircleAlert aria-hidden="true" className="mt-0.5 shrink-0" size={14} />
          {error}
        </p>
      )}
    </div>
  )
}
