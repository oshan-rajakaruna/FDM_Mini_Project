// Illustrative UI-preview values only. These are not model outputs or decision thresholds.
export const RESULT_PREVIEW_STATES = [
  { id: 'idle', label: 'Ready' },
  { id: 'rain-likely', label: 'Rain likely' },
  { id: 'rain-unlikely', label: 'Rain unlikely' },
  { id: 'loading', label: 'Loading' },
  { id: 'error', label: 'Error' },
]

export const DEMO_RESULT_PREVIEWS = {
  'rain-likely': {
    outcome: 'Rain Likely',
    probability: 72,
    riskLevel: 'High',
    recommendation: 'Carry rain protection and review weather-sensitive outdoor plans.',
  },
  'rain-unlikely': {
    outcome: 'Rain Unlikely',
    probability: 24,
    riskLevel: 'Low',
    recommendation: 'Normal plans can generally continue, with local updates checked when conditions matter.',
  },
}
