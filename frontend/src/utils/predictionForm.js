import { WEATHER_STATIONS } from '../data/weatherOptions.js'

export const STEP_FIELDS = [
  ['Date', 'Location', 'RainToday'],
  ['MinTemp', 'MaxTemp', 'Temp9am', 'Temp3pm', 'Rainfall', 'Evaporation', 'Sunshine'],
  [
    'WindGustDir',
    'WindGustSpeed',
    'WindDir9am',
    'WindDir3pm',
    'WindSpeed9am',
    'WindSpeed3pm',
    'Humidity9am',
    'Humidity3pm',
    'Pressure9am',
    'Pressure3pm',
    'Cloud9am',
    'Cloud3pm',
  ],
]

export const FIELD_LABELS = {
  Date: 'Observation date',
  Location: 'Weather station',
  RainToday: 'Rain today',
  MinTemp: 'Minimum temperature',
  MaxTemp: 'Maximum temperature',
  Temp9am: 'Temperature at 9am',
  Temp3pm: 'Temperature at 3pm',
  Rainfall: 'Rainfall',
  Evaporation: 'Evaporation',
  Sunshine: 'Sunshine',
  WindGustDir: 'Wind gust direction',
  WindGustSpeed: 'Wind gust speed',
  WindDir9am: 'Wind direction at 9am',
  WindDir3pm: 'Wind direction at 3pm',
  WindSpeed9am: 'Wind speed at 9am',
  WindSpeed3pm: 'Wind speed at 3pm',
  Humidity9am: 'Humidity at 9am',
  Humidity3pm: 'Humidity at 3pm',
  Pressure9am: 'Pressure at 9am',
  Pressure3pm: 'Pressure at 3pm',
  Cloud9am: 'Cloud cover at 9am',
  Cloud3pm: 'Cloud cover at 3pm',
}

export const NUMERIC_RULES = {
  MinTemp: { step: 0.1, unit: '°C' },
  MaxTemp: { step: 0.1, unit: '°C' },
  Temp9am: { step: 0.1, unit: '°C' },
  Temp3pm: { step: 0.1, unit: '°C' },
  Rainfall: { min: 0, step: 0.1, unit: 'mm' },
  Evaporation: { min: 0, step: 0.1, unit: 'mm' },
  Sunshine: { min: 0, step: 0.1, unit: 'hours' },
  WindGustSpeed: { min: 0, step: 1, unit: 'km/h' },
  WindSpeed9am: { min: 0, step: 1, unit: 'km/h' },
  WindSpeed3pm: { min: 0, step: 1, unit: 'km/h' },
  Humidity9am: { min: 0, max: 100, step: 1, unit: '%' },
  Humidity3pm: { min: 0, max: 100, step: 1, unit: '%' },
  Pressure9am: { minExclusive: 0, step: 0.1, unit: 'hPa' },
  Pressure3pm: { minExclusive: 0, step: 0.1, unit: 'hPa' },
  Cloud9am: { min: 0, max: 8, step: 1, unit: 'oktas' },
  Cloud3pm: { min: 0, max: 8, step: 1, unit: 'oktas' },
}

export const INITIAL_FORM_VALUES = {
  Date: '',
  Location: '',
  RainToday: null,
  MinTemp: null,
  MaxTemp: null,
  Temp9am: null,
  Temp3pm: null,
  Rainfall: null,
  Evaporation: null,
  Sunshine: null,
  WindGustDir: null,
  WindGustSpeed: null,
  WindDir9am: null,
  WindDir3pm: null,
  WindSpeed9am: null,
  WindSpeed3pm: null,
  Humidity9am: null,
  Humidity3pm: null,
  Pressure9am: null,
  Pressure3pm: null,
  Cloud9am: null,
  Cloud3pm: null,
}

export const EXAMPLE_FORM_VALUES = {
  Date: '2016-03-18',
  Location: 'SydneyAirport',
  RainToday: 'No',
  MinTemp: 17.4,
  MaxTemp: 26.8,
  Temp9am: 20.2,
  Temp3pm: 25.1,
  Rainfall: 0.2,
  Evaporation: 5.8,
  Sunshine: 9.1,
  WindGustDir: 'NE',
  WindGustSpeed: 41,
  WindDir9am: 'NNE',
  WindDir3pm: 'ENE',
  WindSpeed9am: 15,
  WindSpeed3pm: 22,
  Humidity9am: 68,
  Humidity3pm: 48,
  Pressure9am: 1015.2,
  Pressure3pm: 1011.6,
  Cloud9am: 3,
  Cloud3pm: 4,
}

export const REVIEW_GROUPS = [
  { title: 'Location & observation', fields: STEP_FIELDS[0], editStep: 0 },
  {
    title: 'Temperature & rain',
    fields: STEP_FIELDS[1],
    editStep: 1,
  },
  {
    title: 'Wind & atmosphere',
    fields: STEP_FIELDS[2],
    editStep: 2,
  },
]

function validateNumericField(name, value) {
  if (value === null) return null
  if (value === '' || !Number.isFinite(Number(value))) {
    return 'Enter a numeric value or mark this field as not available.'
  }

  const number = Number(value)
  const rule = NUMERIC_RULES[name]
  if (rule.min !== undefined && number < rule.min) {
    return `Value must be ${rule.min} or greater.`
  }
  if (rule.minExclusive !== undefined && number <= rule.minExclusive) {
    return 'Value must be greater than zero.'
  }
  if (rule.max !== undefined && number > rule.max) {
    return `Value must be between ${rule.min} and ${rule.max}.`
  }
  return null
}

export function validateStep(stepIndex, values) {
  const errors = {}
  if (stepIndex === 0) {
    if (!values.Date) errors.Date = 'Choose an observation date.'
    if (!values.Location) {
      errors.Location = 'Choose a weather station.'
    } else if (!WEATHER_STATIONS.includes(values.Location)) {
      errors.Location = 'Select a station from the available project locations.'
    }
    return errors
  }

  for (const name of STEP_FIELDS[stepIndex] ?? []) {
    if (NUMERIC_RULES[name]) {
      const error = validateNumericField(name, values[name])
      if (error) errors[name] = error
    }
  }
  return errors
}

export function validateAllSteps(values) {
  for (let stepIndex = 0; stepIndex < STEP_FIELDS.length; stepIndex += 1) {
    const errors = validateStep(stepIndex, values)
    if (Object.keys(errors).length > 0) return { stepIndex, errors }
  }

  return { stepIndex: null, errors: {} }
}

export function normalizeStepValues(stepIndex, values) {
  const normalized = { ...values }
  for (const name of STEP_FIELDS[stepIndex] ?? []) {
    if (NUMERIC_RULES[name] && values[name] !== null && values[name] !== '') {
      normalized[name] = Number(values[name])
    }
  }
  return normalized
}

export function formatReviewValue(name, value) {
  if (value === null || value === '') return 'Not available'
  const rule = NUMERIC_RULES[name]
  if (rule) return `${value} ${rule.unit}`
  return String(value)
}
