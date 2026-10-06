import { STEP_FIELDS } from '../utils/predictionForm.js'
import { ApiError, requestJson } from './apiClient.js'

const PREDICTION_FIELDS = STEP_FIELDS.flat()

export { ApiError as PredictionApiError }

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
    throw new ApiError('The prediction service returned an unexpected response.')
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
  const response = await requestJson('/predict', {
    method: 'POST',
    body: createPredictionPayload(values),
    signal,
    statusMessage: responseErrorMessage,
  })
  return validateResponse(response)
}
