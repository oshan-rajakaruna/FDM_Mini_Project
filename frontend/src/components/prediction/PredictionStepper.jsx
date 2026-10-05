import { Check } from 'lucide-react'

export default function PredictionStepper({ steps, currentStep, furthestStep, onStepSelect }) {
  return (
    <ol className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Prediction progress">
      {steps.map(({ title, shortTitle, icon: Icon }, index) => {
        const active = index === currentStep
        const complete = index < furthestStep
        const disabled = index > furthestStep

        return (
          <li key={title} className="relative">
            <button
              type="button"
              onClick={() => onStepSelect(index)}
              disabled={disabled}
              aria-current={active ? 'step' : undefined}
              aria-label={`Step ${index + 1}: ${title}${complete ? ', completed' : ''}`}
              className={`flex min-h-[4.6rem] w-full items-center gap-3 rounded-2xl border p-4 text-left transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300 disabled:cursor-not-allowed disabled:opacity-45 ${
                active
                  ? 'border-cyan-300/30 bg-cyan-300/10 shadow-[inset_0_-2px_0_rgba(103,232,249,0.65)]'
                  : complete
                    ? 'border-emerald-300/15 bg-emerald-300/[0.055] hover:bg-emerald-300/[0.08]'
                    : 'border-white/10 bg-white/[0.035]'
              }`}
            >
              <span
                className={`grid size-9 shrink-0 place-items-center rounded-xl ${
                  active
                    ? 'bg-cyan-300 text-slate-950'
                    : complete
                      ? 'bg-emerald-300/15 text-emerald-200'
                      : 'bg-white/10 text-slate-500'
                }`}
              >
                {complete ? <Check aria-hidden="true" size={17} /> : <Icon aria-hidden="true" size={18} />}
              </span>
              <span className="min-w-0">
                <span className="block text-[0.62rem] font-extrabold uppercase tracking-[0.18em] text-slate-500">
                  Step {index + 1}
                </span>
                <span className={`mt-1 block truncate text-sm font-bold ${active ? 'text-white' : 'text-slate-300'}`}>
                  {shortTitle ?? title}
                </span>
              </span>
            </button>
            {index < steps.length - 1 && (
              <span className="absolute -right-2 top-1/2 z-10 hidden h-px w-4 bg-white/15 xl:block" aria-hidden="true" />
            )}
          </li>
        )
      })}
    </ol>
  )
}

