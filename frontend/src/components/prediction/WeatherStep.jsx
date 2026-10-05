import { CloudRain, Sun, Thermometer } from 'lucide-react'
import { FIELD_LABELS, NUMERIC_RULES } from '../../utils/predictionForm'
import FormSection from './FormSection'
import NumericField from './NumericField'

const temperatureFields = ['MinTemp', 'MaxTemp', 'Temp9am', 'Temp3pm']
const moistureFields = ['Rainfall', 'Evaporation']

function WeatherNumericField({ name, values, errors, onChange }) {
  return (
    <NumericField
      name={name}
      label={FIELD_LABELS[name]}
      value={values[name]}
      error={errors[name]}
      onChange={onChange}
      {...NUMERIC_RULES[name]}
    />
  )
}

export default function WeatherStep({ values, errors, onChange }) {
  return (
    <div className="space-y-5">
      <FormSection
        icon={Thermometer}
        title="Temperature"
        description="Enter available minimum, maximum, morning, and afternoon temperature observations."
      >
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {temperatureFields.map((name) => (
            <WeatherNumericField key={name} name={name} values={values} errors={errors} onChange={onChange} />
          ))}
        </div>
      </FormSection>

      <div className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
        <FormSection
          icon={CloudRain}
          title="Rain & evaporation"
          description="Record water measurements in millimetres when they are available."
        >
          <div className="grid gap-6 sm:grid-cols-2">
            {moistureFields.map((name) => (
              <WeatherNumericField key={name} name={name} values={values} errors={errors} onChange={onChange} />
            ))}
          </div>
        </FormSection>
        <FormSection
          icon={Sun}
          title="Sunshine"
          description="Add the observed daily sunshine duration."
        >
          <WeatherNumericField name="Sunshine" values={values} errors={errors} onChange={onChange} />
        </FormSection>
      </div>
    </div>
  )
}

