import { CalendarDays, CloudSun, Droplets, Gauge, Info, Search, Thermometer, Wind } from 'lucide-react'
import { motion } from 'framer-motion'
import { useMemo, useState } from 'react'
import SectionHeader from '../components/SectionHeader'

const categories = [
  {
    icon: CalendarDays,
    title: 'Observation',
    hint: 'Required context for the weather record.',
    fields: [
      { name: 'Date', description: 'Calendar date when the weather was observed.' },
      { name: 'Location', description: 'Australian weather station associated with the observation.' },
    ],
  },
  {
    icon: Thermometer,
    title: 'Temperature',
    hint: 'Daily minimums, maximums, and within-day readings.',
    fields: [
      { name: 'MinTemp', description: 'Minimum daily air temperature in °C.' },
      { name: 'MaxTemp', description: 'Maximum daily air temperature in °C.' },
      { name: 'Temp9am', description: 'Air temperature at 9am in °C.' },
      { name: 'Temp3pm', description: 'Air temperature at 3pm in °C.' },
    ],
  },
  {
    icon: Droplets,
    title: 'Rain',
    hint: 'Measured rainfall and the current-day rain label.',
    fields: [
      { name: 'Rainfall', description: 'Rainfall recorded for the day in millimetres.' },
      { name: 'RainToday', description: 'Whether the recorded daily rainfall exceeded 1 mm.' },
    ],
  },
  {
    icon: Droplets,
    title: 'Humidity',
    hint: 'Morning and afternoon moisture levels in the air.',
    fields: [
      { name: 'Humidity9am', description: 'Relative humidity at 9am as a percentage.' },
      { name: 'Humidity3pm', description: 'Relative humidity at 3pm as a percentage.' },
    ],
  },
  {
    icon: Gauge,
    title: 'Pressure',
    hint: 'Atmospheric pressure readings across the day.',
    fields: [
      { name: 'Pressure9am', description: 'Atmospheric pressure at 9am in hPa.' },
      { name: 'Pressure3pm', description: 'Atmospheric pressure at 3pm in hPa.' },
    ],
  },
  {
    icon: Wind,
    title: 'Wind',
    hint: 'Direction, gusts, and morning or afternoon wind speed.',
    fields: [
      { name: 'WindGustDir', description: 'Direction of the strongest wind gust.' },
      { name: 'WindGustSpeed', description: 'Speed of the strongest wind gust in km/h.' },
      { name: 'WindDir9am', description: 'Wind direction at 9am.' },
      { name: 'WindDir3pm', description: 'Wind direction at 3pm.' },
      { name: 'WindSpeed9am', description: 'Wind speed at 9am in km/h.' },
      { name: 'WindSpeed3pm', description: 'Wind speed at 3pm in km/h.' },
    ],
  },
  {
    icon: CloudSun,
    title: 'Sky & water',
    hint: 'Cloud cover, sunshine, and surface-water observations.',
    fields: [
      { name: 'Cloud9am', description: 'Cloud cover at 9am measured from 0 to 8 oktas.' },
      { name: 'Cloud3pm', description: 'Cloud cover at 3pm measured from 0 to 8 oktas.' },
      { name: 'Sunshine', description: 'Bright sunshine duration in hours.' },
      { name: 'Evaporation', description: 'Class A pan evaporation in millimetres.' },
    ],
  },
]

export function filterFieldGuide(query) {
  const term = query.trim().toLowerCase()
  if (!term) return categories

  return categories
    .map((category) => {
      const categoryMatches = `${category.title} ${category.hint}`.toLowerCase().includes(term)
      return {
        ...category,
        fields: categoryMatches
          ? category.fields
          : category.fields.filter(({ name, description }) =>
              `${name} ${description}`.toLowerCase().includes(term),
            ),
      }
    })
    .filter(({ fields }) => fields.length > 0)
}

export default function HelpPage() {
  const [query, setQuery] = useState('')
  const filteredCategories = useMemo(() => filterFieldGuide(query), [query])
  const matchingFieldCount = filteredCategories.reduce((count, category) => count + category.fields.length, 0)

  return (
    <div className="page-container">
      <SectionHeader
        eyebrow="Help & field guide"
        title="Understand every weather input."
        description="Use this field guide to understand the 22 raw observations accepted by the RainWise prediction form."
      />

      <div className="glass-panel mt-10 rounded-[1.5rem] p-4 sm:p-5">
        <label htmlFor="field-search" className="sr-only">Search weather fields</label>
        <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-slate-950/30 px-4 py-3.5 focus-within:border-cyan-300/40 focus-within:ring-2 focus-within:ring-cyan-300/10">
          <Search aria-hidden="true" className="shrink-0 text-slate-500" size={20} />
          <input
            id="field-search"
            type="search"
            placeholder="Search weather fields..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-600"
          />
          <span className="hidden text-xs font-semibold text-slate-500 sm:inline" aria-live="polite">
            {matchingFieldCount} {matchingFieldCount === 1 ? 'field' : 'fields'}
          </span>
        </div>
      </div>

      <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-label="Weather field categories">
        {filteredCategories.map(({ icon: Icon, title, hint, fields }, index) => (
          <motion.article
            key={title}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.055 }}
            className="glass-panel group rounded-2xl p-6 transition hover:border-sky-300/20 hover:bg-white/[0.08]"
          >
            <span className="grid size-12 place-items-center rounded-2xl border border-sky-200/10 bg-sky-300/10 text-cyan-200 transition group-hover:scale-105">
              <Icon aria-hidden="true" size={23} strokeWidth={1.8} />
            </span>
            <h2 className="mt-6 text-lg font-bold text-white">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{hint}</p>
            <dl className="mt-5 space-y-4 border-t border-white/[0.08] pt-5">
              {fields.map(({ name, description }) => (
                <div key={name}>
                  <dt className="text-xs font-extrabold tracking-wide text-sky-100">{name}</dt>
                  <dd className="mt-1 text-xs leading-5 text-slate-400">{description}</dd>
                </div>
              ))}
            </dl>
          </motion.article>
        ))}
      </section>

      {filteredCategories.length === 0 && (
        <div role="status" className="glass-panel mt-8 rounded-2xl p-8 text-center">
          <p className="font-bold text-white">No weather fields match “{query}”.</p>
          <button type="button" onClick={() => setQuery('')} className="secondary-button mt-5">
            Clear search
          </button>
        </div>
      )}

      <aside className="mt-8 flex flex-col gap-4 rounded-2xl border border-indigo-300/15 bg-indigo-300/[0.055] p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-xl bg-indigo-300/10 text-indigo-200">
            <Info aria-hidden="true" size={20} />
          </span>
          <div>
            <p className="text-sm font-bold text-white">Date and Location are required.</p>
            <p className="mt-1 text-xs leading-5 text-slate-400">Every other weather field can be marked Not available; the saved model pipeline handles those missing values.</p>
          </div>
        </div>
      </aside>
    </div>
  )
}

