import { MapPin } from 'lucide-react'

export default function LocationField({ value, error, onChange, stations }) {
  const errorId = 'Location-error'

  return (
    <div>
      <div className="mb-2 flex min-h-5 items-center justify-between gap-3">
        <label htmlFor="Location" className="text-sm font-bold text-slate-200">Weather station</label>
        <span className="text-[0.62rem] font-bold uppercase tracking-[0.12em] text-cyan-200/70">Required</span>
      </div>
      <div className="relative">
        <input
          id="Location"
          name="Location"
          type="text"
          list="weather-station-options"
          autoComplete="off"
          required
          value={value}
          onChange={(event) => onChange('Location', event.target.value)}
          placeholder="Search or select a station"
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : 'Location-hint'}
          className={`field-control pr-11 ${error ? 'border-rose-300/60' : ''}`}
        />
        <MapPin aria-hidden="true" className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500" size={17} />
      </div>
      <datalist id="weather-station-options">
        {stations.map((station) => <option key={station} value={station} />)}
      </datalist>
      <p id="Location-hint" className="mt-2 text-[0.68rem] leading-5 text-slate-600">
        Search the 49 weather-station locations used by the project.
      </p>
      {error && <p id={errorId} role="alert" className="mt-2 text-xs leading-5 text-rose-300">{error}</p>}
    </div>
  )
}

