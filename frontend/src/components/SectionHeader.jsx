export default function SectionHeader({ eyebrow, title, description, align = 'left' }) {
  return (
    <header className={`max-w-[44rem] ${align === 'center' ? 'mx-auto text-center' : ''}`}>
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h2 className="mt-3 text-3xl font-extrabold leading-[1.12] tracking-[-0.04em] text-white sm:text-4xl">
        {title}
      </h2>
      {description && (
        <p className="mt-4 max-w-[42rem] text-sm leading-7 text-slate-400 sm:text-base">{description}</p>
      )}
    </header>
  )
}

