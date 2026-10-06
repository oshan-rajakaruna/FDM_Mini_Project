const STORAGE_KEY = 'rainwise.predictionHistory.v1'
const PREDICTIONS = new Set(['Yes', 'No'])
const RISK_LEVELS = new Set(['Low', 'Moderate', 'High'])

export class HistoryStorageError extends Error {
  constructor(message) {
    super(message)
    this.name = 'HistoryStorageError'
  }
}

function browserStorage() {
  if (typeof window === 'undefined') return null
  try {
    return window.localStorage
  } catch {
    return null
  }
}

function validIsoDate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const parsed = new Date(`${value}T00:00:00Z`)
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value
}

function validRecord(record) {
  return record !== null
    && typeof record === 'object'
    && typeof record.id === 'string'
    && record.id.length > 0
    && typeof record.savedAt === 'string'
    && !Number.isNaN(Date.parse(record.savedAt))
    && validIsoDate(record.observationDate)
    && typeof record.location === 'string'
    && record.location.trim().length > 0
    && PREDICTIONS.has(record.prediction)
    && Number.isFinite(record.rainProbability)
    && record.rainProbability >= 0
    && record.rainProbability <= 1
    && RISK_LEVELS.has(record.riskLevel)
}

function canonicalRecord(record) {
  return {
    id: record.id,
    savedAt: record.savedAt,
    observationDate: record.observationDate,
    location: record.location.trim(),
    prediction: record.prediction,
    rainProbability: record.rainProbability,
    riskLevel: record.riskLevel,
  }
}

function createId(savedAt) {
  if (typeof globalThis.crypto?.randomUUID === 'function') {
    return globalThis.crypto.randomUUID()
  }
  return `${savedAt}-${Math.random().toString(36).slice(2)}`
}

function writeRecords(records, storage) {
  if (!storage) {
    throw new HistoryStorageError('Prediction history is unavailable in this browser.')
  }
  try {
    storage.setItem(STORAGE_KEY, JSON.stringify(records))
  } catch {
    throw new HistoryStorageError('Prediction history could not be saved in this browser.')
  }
}

export function loadPredictionHistory(storage = browserStorage()) {
  if (!storage) return []
  try {
    const parsed = JSON.parse(storage.getItem(STORAGE_KEY) || '[]')
    if (!Array.isArray(parsed)) return []
    return parsed
      .filter(validRecord)
      .map(canonicalRecord)
      .sort((left, right) => Date.parse(right.savedAt) - Date.parse(left.savedAt))
  } catch {
    return []
  }
}

export function savePredictionHistory(input, storage = browserStorage(), now = new Date()) {
  const savedAt = now.toISOString()
  const record = {
    id: createId(savedAt),
    savedAt,
    observationDate: input.observationDate,
    location: input.location,
    prediction: input.prediction,
    rainProbability: input.rainProbability,
    riskLevel: input.riskLevel,
  }
  if (!validRecord(record)) {
    throw new HistoryStorageError('The prediction result is not valid for history storage.')
  }

  const records = [canonicalRecord(record), ...loadPredictionHistory(storage)]
  writeRecords(records, storage)
  return canonicalRecord(record)
}

export function deletePredictionHistory(id, storage = browserStorage()) {
  const records = loadPredictionHistory(storage).filter((record) => record.id !== id)
  writeRecords(records, storage)
  return records
}

export function clearPredictionHistory(storage = browserStorage()) {
  if (!storage) {
    throw new HistoryStorageError('Prediction history is unavailable in this browser.')
  }
  try {
    storage.removeItem(STORAGE_KEY)
  } catch {
    throw new HistoryStorageError('Prediction history could not be cleared in this browser.')
  }
}

export const HISTORY_STORAGE_KEY = STORAGE_KEY
