import {
  ArrowRight,
  Binary,
  BrainCircuit,
  CloudRain,
  DatabaseZap,
  Gauge,
  MapPin,
  ShieldCheck,
  SlidersHorizontal,
  Sprout,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import FeatureCard from '../components/FeatureCard'
import HeroSection from '../components/HeroSection'
import SectionHeader from '../components/SectionHeader'

const features = [
  {
    icon: CloudRain,
    title: 'Next-Day Rain Prediction',
    description: 'Translate current weather conditions into a focused Rain or No Rain outlook for tomorrow.',
  },
  {
    icon: Gauge,
    title: 'Rain Probability',
    description: 'Present model confidence in a format designed to support informed, proportionate decisions.',
  },
  {
    icon: ShieldCheck,
    title: 'Weather-Risk Guidance',
    description: 'Turn an outlook into practical context for planning travel, work, events, and daily routines.',
  },
  {
    icon: MapPin,
    title: 'Location-Aware Inputs',
    description: 'Structure weather observations around the selected Australian location and local conditions.',
  },
]

const workflow = [
  { icon: Sprout, label: "Today's Weather", note: 'Observed conditions' },
  { icon: SlidersHorizontal, label: 'Preprocessing', note: 'Clean, consistent inputs' },
  { icon: BrainCircuit, label: 'Machine Learning', note: 'Pattern recognition' },
  { icon: CloudRain, label: "Tomorrow's Prediction", note: 'Rain or No Rain' },
  { icon: ShieldCheck, label: 'Planning Guidance', note: 'Decision-ready context' },
]

export default function HomePage() {
  return (
    <div className="page-container">
      <HeroSection />

      <section className="py-16 sm:py-20">
        <SectionHeader
          eyebrow="RainWise capabilities"
          title="Weather signals, made decision-ready."
          description="A focused experience that brings prediction, probability, and practical weather-risk context together without overwhelming the user."
        />
        <div className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {features.map((feature, index) => (
            <FeatureCard key={feature.title} {...feature} index={index} />
          ))}
        </div>
      </section>

      <section id="how-it-works" className="scroll-mt-8 py-10 lg:py-14">
        <SectionHeader
          eyebrow="How it works"
          title="From observation to action."
          description="RainWise follows a clear pipeline that keeps the experience understandable while the modeling happens behind the scenes."
        />
        <div className="glass-panel mt-10 rounded-[1.75rem] p-5 sm:p-7 lg:p-9">
          <div className="grid gap-3 lg:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr_auto_1fr] lg:items-center">
            {workflow.map(({ icon: Icon, label, note }, index) => (
              <div key={label} className="contents">
                <div className="rounded-2xl border border-white/10 bg-slate-950/20 p-4 lg:min-h-40 lg:p-5">
                  <span className="grid size-10 place-items-center rounded-xl bg-sky-300/10 text-cyan-200">
                    <Icon aria-hidden="true" size={20} strokeWidth={1.8} />
                  </span>
                  <p className="mt-6 text-sm font-bold leading-5 text-white">{label}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-400">{note}</p>
                </div>
                {index < workflow.length - 1 && (
                  <ArrowRight
                    aria-hidden="true"
                    className="mx-auto rotate-90 text-sky-300/50 lg:rotate-0"
                    size={20}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-5 py-16 sm:py-20 lg:grid-cols-[1fr_0.78fr]">
        <div className="relative overflow-hidden rounded-[1.75rem] border border-cyan-200/15 bg-sky-300/[0.07] p-7 sm:p-9">
          <div className="absolute -right-16 -top-16 size-56 rounded-full bg-sky-400/10 blur-3xl" />
          <p className="eyebrow">Built for clarity</p>
          <h2 className="relative mt-4 max-w-xl text-3xl font-extrabold tracking-[-0.04em] text-white sm:text-4xl">
            Start with a guided weather review.
          </h2>
          <p className="relative mt-4 max-w-2xl text-sm leading-7 text-slate-300">
            The prediction workspace guides you through location, weather, wind, and atmospheric observations before sending a reviewed request to the local RainWise service.
          </p>
          <Link to="/predict" className="primary-button relative mt-7">
            Open prediction workspace <ArrowRight size={18} />
          </Link>
        </div>

        <aside className="glass-panel rounded-[1.75rem] p-7 sm:p-9" aria-label="Model information">
          <div className="flex items-center justify-between">
            <span className="grid size-12 place-items-center rounded-2xl bg-indigo-300/10 text-indigo-200">
              <DatabaseZap aria-hidden="true" size={23} />
            </span>
            <span className="rounded-full border border-emerald-300/15 bg-emerald-300/10 px-3 py-1 text-[0.68rem] font-bold uppercase tracking-[0.14em] text-emerald-200">
              Final model
            </span>
          </div>
          <dl className="mt-8 space-y-5">
            <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-5">
              <dt className="text-sm text-slate-400">Model</dt>
              <dd className="text-sm font-bold text-white">Random Forest</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt className="flex items-center gap-2 text-sm text-slate-400">
                <Binary size={16} /> Output
              </dt>
              <dd className="text-sm font-bold text-white">Rain / No Rain</dd>
            </div>
          </dl>
        </aside>
      </section>
    </div>
  )
}

