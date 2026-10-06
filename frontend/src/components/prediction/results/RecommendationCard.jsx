import { Lightbulb } from 'lucide-react'

export default function RecommendationCard({ recommendation }) {
  return (
    <section className="rounded-2xl border border-cyan-300/15 bg-cyan-300/[0.065] p-5" aria-labelledby="recommendation-heading">
      <div className="flex items-start gap-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-cyan-300/10 text-cyan-200">
          <Lightbulb aria-hidden="true" size={19} />
        </span>
        <div>
          <h4 id="recommendation-heading" className="text-sm font-bold text-white">Planning recommendation</h4>
          <p className="mt-2 text-sm leading-6 text-slate-300">{recommendation}</p>
          <p className="mt-3 text-[0.68rem] leading-5 text-slate-400">
            Decision-support guidance only. Weather conditions can change.
          </p>
        </div>
      </div>
    </section>
  )
}
