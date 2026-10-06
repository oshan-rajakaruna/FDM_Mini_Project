import { STEP_FIELDS } from '../utils/predictionForm.js'

const API_BASE_URL = (import.meta.env?.VITE_RAINWISE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
const PREDICTION_FIELDS = STEP_FIELDS.flat()

export class PredictionApiError extends Error {
  constructor(message, status = null) {
    super(message)
    this.name = 'PredictionApiError'
    this.status = status
  }
}

export function createPredictionPayload(values) {
  return Object.fromEntries(
    PREDICTION_FIELDS.map((field) => [field, values[field] ?? null]),
  )
}

function validateResponse(data) {
  const validPrediction = data?.prediction === 'Yes' || data?.prediction === 'No'
  const validProbability = Number.isFinite(data?.rain_probability)
    && data.rain_probability >= 0
    && data.rain_probability <= 1
  const validThreshold = Number.isFinite(data?.threshold)
    && data.threshold >= 0
    && data.threshold <= 1
  const validPositiveClass = data?.positive_class === 'Yes'

  if (!validPrediction || !validProbability || !validThreshold || !validPositiveClass) {
    throw new PredictionApiError('The prediction service returned an unexpected response.')
  }

  return data
}

function responseErrorMessage(status, body) {
  if (status === 422) {
    const detail = typeof body?.detail === 'string' ? ` ${body.detail}` : ''
    return `The backend rejected one or more weather inputs.${detail}`
  }
  if (status >= 500) {
    return 'The RainWise prediction service could not complete this request. Please try again.'
  }
  return `The prediction request failed with status ${status}.`
}

export async function requestPrediction(values, { signal } = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(createPredictionPayload(values)),
      signal,
    })
    const body = await response.json().catch(() => null)

    if (!response.ok) {
      throw new PredictionApiError(responseErrorMessage(response.status, body), response.status)
    }

    return validateResponse(body)
  } catch (error) {
    if (error?.name === 'AbortError' || error instanceof PredictionApiError) throw error
    throw new PredictionApiError(
      'Unable to reach the RainWise backend. Confirm the local API is running and try again.',
    )
  }
}
