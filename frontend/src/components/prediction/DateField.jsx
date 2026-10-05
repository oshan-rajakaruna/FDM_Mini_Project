import { CalendarDays } from 'lucide-react'

export default function DateField({ value, error, onChange }) {
  const errorId = 'Date-error'

  return (
    <div>
      <div className="mb-2 flex min-h-5 items-center justify-between gap-3">
        <label htmlFor="Date" className="text-sm font-bold text-slate-200">Observation date</label>
        <span className="text-[0.62rem] font-bold uppercase tracking-[0.12em] text-cyan-200/70">Required</span>
      </div>
      <div className="relative">
        <input
          id="Date"
          name="Date"
          type="date"
          required
          value={value}
          onChange={(event) => onChange('Date', event.target.value)}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
          className={`field-control pr-11 ${error ? 'border-rose-300/60' : ''}`}
        />
        <CalendarDays aria-hidden="true" className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500" size={17} />
      </div>
      <p className="mt-2 text-[0.68rem] leading-5 text-slate-500">Use the date these weather conditions were observed.</p>
      {error && <p id={errorId} role="alert" className="mt-2 text-xs leading-5 text-rose-300">{error}</p>}
    </div>
  )
}

