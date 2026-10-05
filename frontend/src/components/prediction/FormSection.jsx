export default function FormSection({ icon: Icon, title, description, children }) {
  const headingId = `${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-heading`

  return (
    <section className="glass-panel rounded-[1.5rem] p-5 sm:p-7" aria-labelledby={headingId}>
      <header className="flex items-start gap-4 border-b border-white/10 pb-5">
        <span className="grid size-11 shrink-0 place-items-center rounded-xl border border-sky-300/15 bg-sky-300/10 text-cyan-200">
          <Icon aria-hidden="true" size={21} strokeWidth={1.8} />
        </span>
        <div>
          <h2 id={headingId} className="text-base font-bold text-white">
            {title}
          </h2>
          {description && <p className="mt-1 text-xs leading-5 text-slate-400">{description}</p>}
        </div>
      </header>
      <div className="mt-6">{children}</div>
    </section>
  )
}
