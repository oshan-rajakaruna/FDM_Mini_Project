import { AlertTriangle, RotateCcw } from 'lucide-react'

export default function ResultErrorState({ message, onReset }) {
  return (
    <div className="rounded-[1.5rem] border border-rose-300/20 bg-rose-300/[0.055] p-7 sm:p-10" role="alert">
      <div className="mx-auto flex max-w-lg flex-col items-center text-center">
        <span className="grid size-14 place-items-center rounded-2xl bg-rose-300/10 text-rose-200">
          <AlertTriangle aria-hidden="true" size={25} />
        </span>
        <h3 className="mt-5 text-lg font-extrabold text-white">Result unavailable</h3>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          {message || 'The prediction request could not be completed. Please try again.'}
        </p>
        <button type="button" onClick={onReset} className="secondary-button mt-6">
          <RotateCcw aria-hidden="true" size={16} /> Dismiss and try again
        </button>
      </div>
    </div>
  )
}
