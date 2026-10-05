import { CircleCheck, CloudOff } from 'lucide-react'
import { REVIEW_GROUPS } from '../../utils/predictionForm'
import ReviewCard from './ReviewCard'

export default function ReviewStep({ values, onEdit, notice }) {
  return (
    <div className="space-y-5">
      <div className="grid gap-5 xl:grid-cols-2">
        {REVIEW_GROUPS.map((group, index) => (
          <div key={group.title} className={index === REVIEW_GROUPS.length - 1 ? 'xl:col-span-2' : ''}>
            <ReviewCard
              title={group.title}
              fields={group.fields}
              values={values}
              onEdit={() => onEdit(group.editStep)}
            />
          </div>
        ))}
      </div>

      {notice && (
        <div role="status" aria-live="polite" className="flex items-start gap-3 rounded-2xl border border-cyan-300/20 bg-cyan-300/[0.08] p-5 text-sm text-cyan-50">
          <CircleCheck aria-hidden="true" className="mt-0.5 shrink-0 text-cyan-200" size={20} />
          <div>
            <p className="font-bold">Form review complete</p>
            <p className="mt-1 leading-6 text-cyan-100/70">{notice}</p>
          </div>
        </div>
      )}

      <div className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.035] p-5 text-sm text-slate-400">
        <CloudOff aria-hidden="true" className="mt-0.5 shrink-0 text-slate-500" size={20} />
        <p className="leading-6">
          No prediction is generated in this frontend-only stage. Your inputs remain in this browser session and are not sent anywhere.
        </p>
      </div>
    </div>
  )
}

