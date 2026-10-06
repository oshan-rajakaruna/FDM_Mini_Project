export const API_BASE_URL = (
  import.meta.env?.VITE_RAINWISE_API_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function requestJson(
  path,
  {
    method = 'GET',
    body,
    signal,
    statusMessage,
    networkMessage = 'Unable to reach the RainWise backend. Confirm the local API is running and try again.',
  } = {},
) {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
    const responseBody = await response.json().catch(() => null)

    if (!response.ok) {
      const message = statusMessage?.(response.status, responseBody)
        || `The RainWise request failed with status ${response.status}.`
      throw new ApiError(message, response.status)
    }

    return responseBody
  } catch (error) {
    if (error?.name === 'AbortError' || error instanceof ApiError) throw error
    throw new ApiError(networkMessage)
  }
}
