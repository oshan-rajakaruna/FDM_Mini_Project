export function getDisplayRiskLevel(probability) {
  if (probability < 0.33) return 'Low'
  if (probability < 0.67) return 'Moderate'
  return 'High'
}
