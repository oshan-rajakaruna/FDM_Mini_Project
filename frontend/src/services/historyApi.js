import { ApiError, requestJson } from './apiClient.js'

const PUBLIC_FIELDS = [
  'id',
  'observationDate',
  'location',
  'prediction',
  'rainProbability',
  'createdAt',
]

function validIsoDate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const parsed = new Date(`${value}T00:00:00Z`)
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value
}

function validHistoryRecord(record) {
  return record !== null
    && typeof record === 'object'
    && PUBLIC_FIELDS.every((field) => Object.hasOwn(record, field))
    && typeof record.id === 'string'
    && record.id.length > 0
    && validIsoDate(record.observationDate)
    && typeof record.location === 'string'
    && record.location.trim().length > 0
    && (record.prediction === 'Yes' || record.prediction === 'No')
    && Number.isFinite(record.rainProbability)
    && record.rainProbability >= 0
    && record.rainProbability <= 1
    && typeof record.createdAt === 'string'
    && !Number.isNaN(Date.parse(record.createdAt))
}

function validateHistory(records) {
  if (!Array.isArray(records) || !records.every(validHistoryRecord)) {
    throw new ApiError('The prediction history service returned an unexpected response.')
  }
  return records
}

function historyStatusMessage(status) {
  if (status === 400) return 'This prediction history item could not be identified.'
  if (status === 404) return 'This prediction is no longer in history.'
  if (status >= 500) return 'Prediction history is temporarily unavailable. Please try again.'
  return `The prediction history request failed with status ${status}.`
}

const historyNetworkMessage = 'Unable to reach prediction history. Confirm the local RainWise backend is running and try again.'

export async function fetchPredictionHistory({ signal } = {}) {
  const records = await requestJson('/history', {
    signal,
    statusMessage: historyStatusMessage,
    networkMessage: historyNetworkMessage,
  })
  return validateHistory(records)
}

export async function deletePredictionHistory(id, { signal } = {}) {
  const response = await requestJson(`/history/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    signal,
    statusMessage: historyStatusMessage,
    networkMessage: historyNetworkMessage,
  })
  if (response?.deleted !== true || response?.id !== id) {
    throw new ApiError('The prediction history service returned an unexpected response.')
  }
  return response
}

export async function clearPredictionHistory({ signal } = {}) {
  const response = await requestJson('/history', {
    method: 'DELETE',
    signal,
    statusMessage: historyStatusMessage,
    networkMessage: historyNetworkMessage,
  })
  if (!Number.isInteger(response?.deletedCount) || response.deletedCount < 0) {
    throw new ApiError('The prediction history service returned an unexpected response.')
  }
  return response
}
