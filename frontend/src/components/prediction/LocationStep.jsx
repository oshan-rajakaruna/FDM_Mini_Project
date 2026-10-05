import { MapPin } from 'lucide-react'
import { RAIN_TODAY_OPTIONS, WEATHER_STATIONS } from '../../data/weatherOptions'
import DateField from './DateField'
import FormSection from './FormSection'
import LocationField from './LocationField'
import SelectField from './SelectField'

export default function LocationStep({ values, errors, onChange }) {
  return (
    <FormSection
      icon={MapPin}
      title="Location & observation"
      description="Set the place and date for today’s weather record. Rain today can be left unavailable."
    >
      <div className="grid gap-6 lg:grid-cols-3">
        <DateField value={values.Date} error={errors.Date} onChange={onChange} />
        <LocationField value={values.Location} error={errors.Location} onChange={onChange} stations={WEATHER_STATIONS} />
        <SelectField
          name="RainToday"
          label="Rain today"
          value={values.RainToday}
          options={RAIN_TODAY_OPTIONS}
          error={errors.RainToday}
          onChange={onChange}
        />
      </div>
    </FormSection>
  )
}

