import { Cloudy, Compass, Droplets, Gauge, Wind } from 'lucide-react'
import { WIND_DIRECTIONS } from '../../data/weatherOptions'
import { FIELD_LABELS, NUMERIC_RULES } from '../../utils/predictionForm'
import FormSection from './FormSection'
import NumericField from './NumericField'
import SelectField from './SelectField'

const directionFields = ['WindGustDir', 'WindDir9am', 'WindDir3pm']
const speedFields = ['WindGustSpeed', 'WindSpeed9am', 'WindSpeed3pm']
const humidityFields = ['Humidity9am', 'Humidity3pm']
const pressureFields = ['Pressure9am', 'Pressure3pm']
const cloudFields = ['Cloud9am', 'Cloud3pm']

function AtmosphericNumericField({ name, values, errors, onChange }) {
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

export default function AtmosphereStep({ values, errors, onChange }) {
  return (
    <div className="space-y-5">
      <div className="grid gap-5 xl:grid-cols-2">
        <FormSection
          icon={Compass}
          title="Wind direction"
          description="Choose the gust, morning, and afternoon compass directions."
        >
          <div className="grid gap-6 sm:grid-cols-3">
            {directionFields.map((name) => (
              <SelectField
                key={name}
                name={name}
                label={FIELD_LABELS[name]}
                value={values[name]}
                options={WIND_DIRECTIONS}
                error={errors[name]}
                onChange={onChange}
              />
            ))}
          </div>
        </FormSection>

        <FormSection
          icon={Wind}
          title="Wind speed"
          description="Add available gust, morning, and afternoon wind speeds."
        >
          <div className="grid gap-6 sm:grid-cols-3">
            {speedFields.map((name) => (
              <AtmosphericNumericField key={name} name={name} values={values} errors={errors} onChange={onChange} />
            ))}
          </div>
        </FormSection>
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        <FormSection icon={Droplets} title="Humidity" description="Relative humidity from 0 to 100 percent.">
          <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            {humidityFields.map((name) => (
              <AtmosphericNumericField key={name} name={name} values={values} errors={errors} onChange={onChange} />
            ))}
          </div>
        </FormSection>
        <FormSection icon={Gauge} title="Pressure" description="Positive atmospheric pressure readings in hPa.">
          <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            {pressureFields.map((name) => (
              <AtmosphericNumericField key={name} name={name} values={values} errors={errors} onChange={onChange} />
            ))}
          </div>
        </FormSection>
        <FormSection icon={Cloudy} title="Cloud cover" description="Cloud amount from 0 to 8 oktas.">
          <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            {cloudFields.map((name) => (
              <AtmosphericNumericField key={name} name={name} values={values} errors={errors} onChange={onChange} />
            ))}
          </div>
        </FormSection>
      </div>
    </div>
  )
}

