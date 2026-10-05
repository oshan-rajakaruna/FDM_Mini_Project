import { CloudRain, CloudSun } from 'lucide-react'
import ProbabilityGauge from './ProbabilityGauge'
import RecommendationCard from './RecommendationCard'
import RiskLevelDisplay from './RiskLevelDisplay'

export default function OutcomeSummary({ result }) {
  const rainLikely = result.outcome === 'Rain Likely'
  const OutcomeIcon = rainLikely ? CloudRain : CloudSun

  return (
    <section className="glass-panel rounded-[1.5rem] p-5 sm:p-7" aria-labelledby="prediction-outcome-heading">
      <div className="flex flex-col items-center gap-7 xl:flex-row xl:items-stretch">
        <div className="flex w-full flex-col items-center justify-center rounded-2xl border border-white/[0.07] bg-slate-950/20 p-5 sm:flex-row sm:gap-7 xl:w-auto xl:min-w-[22rem] xl:flex-col">
          <ProbabilityGauge probability={result.probability} />
          <div className="mt-4 text-center sm:mt-0 xl:mt-4">
            <span className={`mx-auto grid size-11 place-items-center rounded-xl ${rainLikely ? 'bg-sky-300/12 text-sky-200' : 'bg-emerald-300/12 text-emerald-200'}`}>
              <OutcomeIcon aria-hidden="true" size={22} />
            </span>
            <h3 id="prediction-outcome-heading" className="mt-3 text-2xl font-extrabold tracking-tight text-white">
              {result.outcome}
            </h3>
            <p className="mt-1 text-xs text-slate-500">Illustrative UI value—not model output</p>
          </div>
        </div>

        <div className="grid w-full min-w-0 gap-5 xl:grid-cols-2">
          <div className="rounded-2xl border border-white/[0.07] bg-white/[0.025] p-5">
            <RiskLevelDisplay level={result.riskLevel} />
          </div>
          <RecommendationCard recommendation={result.recommendation} />
        </div>
      </div>
    </section>
  )
}
