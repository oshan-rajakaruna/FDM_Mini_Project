import { Pencil } from 'lucide-react'
import { FIELD_LABELS, formatReviewValue } from '../../utils/predictionForm'

export default function ReviewCard({ title, fields, values, onEdit }) {
  return (
    <section className="glass-panel rounded-[1.5rem] p-5 sm:p-6">
      <header className="flex items-center justify-between gap-4 border-b border-white/10 pb-4">
        <h2 className="text-base font-bold text-white">{title}</h2>
        <button
          type="button"
          onClick={onEdit}
          className="inline-flex min-h-9 items-center gap-2 rounded-lg border border-white/10 px-3 text-xs font-bold text-slate-300 transition hover:border-cyan-300/25 hover:bg-cyan-300/10 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300"
        >
          <Pencil aria-hidden="true" size={14} /> Edit
        </button>
      </header>
      <dl className="mt-4 grid gap-x-6 sm:grid-cols-2">
        {fields.map((name) => {
          const missing = values[name] === null || values[name] === ''
          return (
            <div key={name} className="flex min-h-12 min-w-0 items-center justify-between gap-4 border-b border-white/[0.07] py-3 text-sm">
              <dt className="min-w-0 text-slate-400">{FIELD_LABELS[name]}</dt>
              <dd className={`min-w-0 break-words text-right font-semibold ${missing ? 'italic text-slate-400' : 'text-slate-200'}`}>
                {formatReviewValue(name, values[name])}
              </dd>
            </div>
          )
        })}
      </dl>
    </section>
  )
}

