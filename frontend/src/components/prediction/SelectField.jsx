import { ChevronDown } from 'lucide-react'

export default function SelectField({ name, label, value, options, error, onChange, optional = true }) {
  const errorId = `${name}-error`

  return (
    <div>
      <div className="mb-2 flex min-h-5 items-center justify-between gap-3">
        <label htmlFor={name} className="text-sm font-bold text-slate-200">{label}</label>
        {optional && (
          <span className="text-[0.62rem] font-bold uppercase tracking-[0.12em] text-slate-600">Optional</span>
        )}
      </div>
      <div className="relative">
        <select
          id={name}
          name={name}
          value={value ?? ''}
          onChange={(event) => onChange(name, event.target.value || null)}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
          className={`field-control appearance-none pr-10 ${error ? 'border-rose-300/60' : ''}`}
        >
          {optional && <option value="">Not available</option>}
          {!optional && <option value="">Select an option</option>}
          {options.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
        <ChevronDown aria-hidden="true" className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500" size={17} />
      </div>
      {optional && <p className="mt-2 text-[0.68rem] leading-5 text-slate-600">Choose Not available when this observation is missing.</p>}
      {error && <p id={errorId} role="alert" className="mt-2 text-xs leading-5 text-rose-300">{error}</p>}
    </div>
  )
}

