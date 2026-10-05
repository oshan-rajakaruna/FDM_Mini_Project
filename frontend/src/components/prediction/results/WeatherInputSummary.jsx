import { ClipboardList } from 'lucide-react'
import { FIELD_LABELS, formatReviewValue } from '../../../utils/predictionForm'

const SUMMARY_FIELDS = [
  'Date',
  'Location',
  'RainToday',
  'MinTemp',
  'MaxTemp',
  'Rainfall',
  'Humidity3pm',
  'WindGustSpeed',
]

export default function WeatherInputSummary({ values }) {
  return (
    <section className="glass-panel rounded-2xl p-5 sm:p-6" aria-labelledby="weather-summary-heading">
      <div className="flex items-center gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-white/[0.06] text-sky-200">
          <ClipboardList aria-hidden="true" size={17} />
        </span>
        <div>
          <h4 id="weather-summary-heading" className="text-sm font-bold text-white">Weather input summary</h4>
          <p className="mt-0.5 text-xs text-slate-500">Key observations used in this interface preview.</p>
        </div>
      </div>
      <dl className="mt-4 grid gap-x-6 sm:grid-cols-2 xl:grid-cols-4">
        {SUMMARY_FIELDS.map((name) => (
          <div key={name} className="min-w-0 border-b border-white/[0.07] py-3">
            <dt className="text-[0.68rem] font-semibold text-slate-500">{FIELD_LABELS[name]}</dt>
            <dd className="mt-1 break-words text-sm font-bold text-slate-200">{formatReviewValue(name, values[name])}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
