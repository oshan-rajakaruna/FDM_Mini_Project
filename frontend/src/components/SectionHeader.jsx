export default function SectionHeader({ eyebrow, title, description, align = 'left' }) {
  return (
    <header className={`max-w-2xl ${align === 'center' ? 'mx-auto text-center' : ''}`}>
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h2 className="mt-3 text-3xl font-extrabold tracking-[-0.035em] text-white sm:text-4xl">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-sm leading-7 text-slate-400 sm:text-base">{description}</p>
      )}
    </header>
  )
}

