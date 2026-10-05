import { LoaderCircle } from 'lucide-react'

export default function ResultLoadingState() {
  return (
    <div className="glass-panel rounded-[1.5rem] p-7 sm:p-10" role="status" aria-live="polite" aria-busy="true">
      <div className="mx-auto flex max-w-md flex-col items-center text-center">
        <span className="grid size-14 place-items-center rounded-2xl border border-cyan-300/20 bg-cyan-300/[0.08] text-cyan-200">
          <LoaderCircle aria-hidden="true" className="animate-spin" size={25} />
        </span>
        <h3 className="mt-5 text-lg font-extrabold text-white">Preparing the result view</h3>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          Loading-state preview only. No request is being sent and no model is running.
        </p>
        <div className="mt-7 grid w-full gap-3 sm:grid-cols-3" aria-hidden="true">
          {[0, 1, 2].map((item) => (
            <span key={item} className="h-16 animate-pulse rounded-xl bg-white/[0.045]" />
          ))}
        </div>
      </div>
    </div>
  )
}
