import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowLeft,
  ArrowRight,
  Beaker,
  Check,
  CloudRain,
  Info,
  ListChecks,
  MapPin,
  RefreshCcw,
  ShieldCheck,
  Thermometer,
  Wind,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import AtmosphereStep from '../components/prediction/AtmosphereStep'
import LocationStep from '../components/prediction/LocationStep'
import PredictionStepper from '../components/prediction/PredictionStepper'
import PredictionResultSection from '../components/prediction/results/PredictionResultSection'
import ReviewStep from '../components/prediction/ReviewStep'
import WeatherStep from '../components/prediction/WeatherStep'
import SectionHeader from '../components/SectionHeader'
import {
  DEMO_FORM_VALUES,
  INITIAL_FORM_VALUES,
  normalizeStepValues,
  validateAllSteps,
  validateStep,
} from '../utils/predictionForm'

const steps = [
  { title: 'Location & Observation', shortTitle: 'Location', icon: MapPin },
  { title: 'Temperature & Rain', shortTitle: 'Weather', icon: Thermometer },
  { title: 'Wind & Atmosphere', shortTitle: 'Wind & Atmosphere', icon: Wind },
  { title: 'Review & Predict', shortTitle: 'Review & Predict', icon: ListChecks },
]

export default function PredictPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const [furthestStep, setFurthestStep] = useState(0)
  const [values, setValues] = useState(() => ({ ...INITIAL_FORM_VALUES }))
  const [errors, setErrors] = useState({})
  const [demoLoaded, setDemoLoaded] = useState(false)
  const [notice, setNotice] = useState('')
  const [resultPreviewState, setResultPreviewState] = useState('idle')

  useEffect(() => {
    const firstField = Object.keys(errors)[0]
    if (!firstField) return undefined

    let frameId
    let attempts = 0
    const focusWhenReady = () => {
      const field = document.getElementById(firstField)
      if (field) {
        field.focus()
        return
      }
      attempts += 1
      if (attempts < 30) frameId = window.requestAnimationFrame(focusWhenReady)
    }

    frameId = window.requestAnimationFrame(focusWhenReady)
    return () => window.cancelAnimationFrame(frameId)
  }, [currentStep, errors])

  const handleChange = (name, value) => {
    setValues((current) => ({ ...current, [name]: value }))
    setErrors((current) => {
      if (!current[name]) return current
      const next = { ...current }
      delete next[name]
      return next
    })
    setNotice('')
    setResultPreviewState('idle')
  }

  const validateAndNormalizeCurrentStep = () => {
    const stepErrors = validateStep(currentStep, values)
    if (Object.keys(stepErrors).length > 0) {
      setErrors(stepErrors)
      return false
    }
    setValues((current) => normalizeStepValues(currentStep, current))
    setErrors({})
    return true
  }

  const handleNext = () => {
    if (!validateAndNormalizeCurrentStep()) return
    const nextStep = Math.min(currentStep + 1, steps.length - 1)
    setCurrentStep(nextStep)
    setFurthestStep((current) => Math.max(current, nextStep))
    setNotice('')
  }

  const handleBack = () => {
    setCurrentStep((current) => Math.max(0, current - 1))
    setErrors({})
    setNotice('')
  }

  const handleStepSelect = (stepIndex) => {
    if (stepIndex === currentStep || stepIndex > furthestStep) return
    if (stepIndex > currentStep && !validateAndNormalizeCurrentStep()) return
    setCurrentStep(stepIndex)
    setErrors({})
    setNotice('')
  }

  const handleReset = () => {
    setValues({ ...INITIAL_FORM_VALUES })
    setErrors({})
    setCurrentStep(0)
    setFurthestStep(0)
    setDemoLoaded(false)
    setNotice('')
    setResultPreviewState('idle')
  }

  const handleLoadExample = () => {
    setValues({ ...DEMO_FORM_VALUES })
    setErrors({})
    setCurrentStep(0)
    setFurthestStep(0)
    setDemoLoaded(true)
    setNotice('')
    setResultPreviewState('idle')
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    if (currentStep < steps.length - 1) {
      handleNext()
      return
    }

    const finalValidation = validateAllSteps(values)
    if (finalValidation.stepIndex !== null) {
      setCurrentStep(finalValidation.stepIndex)
      setErrors(finalValidation.errors)
      setNotice('')
      return
    }

    setNotice('Prediction service will be connected in the next integration step.')
  }

  return (
    <div className="page-container">
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem] lg:items-end">
        <SectionHeader
          eyebrow="Prediction workspace"
          title="Build tomorrow’s rainfall outlook."
          description="Enter today’s raw weather observations through a guided four-step review. Missing-capable measurements can be marked as unavailable."
        />
        <aside className="flex gap-3 rounded-2xl border border-sky-300/15 bg-sky-300/[0.055] p-4 text-xs leading-5 text-slate-400">
          <ShieldCheck aria-hidden="true" className="mt-0.5 shrink-0 text-cyan-200" size={19} />
          <p>
            Values stay in this frontend only. Nothing is submitted to a prediction service in this stage.
          </p>
        </aside>
      </div>

      <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
          <Info aria-hidden="true" size={15} />
          Required fields are identified; all other inputs support missing values.
        </div>
        <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
          <button type="button" onClick={handleReset} className="secondary-button min-h-10 px-3.5 py-2 text-xs">
            <RefreshCcw aria-hidden="true" size={15} /> Reset Form
          </button>
          <button type="button" onClick={handleLoadExample} className="secondary-button min-h-10 px-3.5 py-2 text-xs">
            <Beaker aria-hidden="true" size={15} /> Load Example
          </button>
        </div>
      </div>

      {demoLoaded && (
        <div role="status" className="mt-5 flex items-center gap-3 rounded-2xl border border-amber-300/20 bg-amber-300/[0.07] px-4 py-3 text-xs text-amber-100/80">
          <Beaker aria-hidden="true" className="shrink-0 text-amber-200" size={18} />
          <p>
            <strong className="font-extrabold uppercase tracking-[0.12em] text-amber-200">Demo sample data</strong>
            <span className="ml-2">Plausible values for interface demonstration only—not a real weather observation.</span>
          </p>
        </div>
      )}

      <div className="mt-7">
        <PredictionStepper
          steps={steps}
          currentStep={currentStep}
          furthestStep={furthestStep}
          onStepSelect={handleStepSelect}
        />
      </div>

      <form onSubmit={handleSubmit} noValidate className="mt-7">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 18 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
          >
            {currentStep === 0 && <LocationStep values={values} errors={errors} onChange={handleChange} />}
            {currentStep === 1 && <WeatherStep values={values} errors={errors} onChange={handleChange} />}
            {currentStep === 2 && <AtmosphereStep values={values} errors={errors} onChange={handleChange} />}
            {currentStep === 3 && (
              <ReviewStep values={values} onEdit={setCurrentStep} notice={notice} />
            )}
          </motion.div>
        </AnimatePresence>

        <div className="glass-panel mt-5 flex flex-col-reverse gap-3 rounded-2xl p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
          <button
            type="button"
            onClick={handleBack}
            disabled={currentStep === 0}
            className="secondary-button disabled:cursor-not-allowed disabled:opacity-35"
          >
            <ArrowLeft aria-hidden="true" size={17} /> Back
          </button>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
            <span className="text-center text-xs font-semibold text-slate-500 sm:text-left">
              Step {currentStep + 1} of {steps.length}
            </span>
            {currentStep < steps.length - 1 ? (
              <button type="submit" className="primary-button w-full sm:w-auto">
                Continue <ArrowRight aria-hidden="true" size={17} />
              </button>
            ) : (
              <button type="submit" className="primary-button w-full sm:w-auto">
                <CloudRain aria-hidden="true" size={18} /> Predict Tomorrow&apos;s Rain
              </button>
            )}
          </div>
        </div>
      </form>

      {currentStep === steps.length - 1 && (
        <PredictionResultSection
          previewState={resultPreviewState}
          onPreviewStateChange={setResultPreviewState}
          previewEnabled={demoLoaded}
          values={values}
        />
      )}

      <p className="mt-4 flex items-center justify-center gap-2 text-center text-[0.68rem] leading-5 text-slate-600">
        <Check aria-hidden="true" size={13} /> Raw weather inputs only—no engineered, encoded, or scaled values are requested.
      </p>
    </div>
  )
}
