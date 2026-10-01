const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Fire-and-forget: wakes the free-tier backend while the user fills in the form.
export function warmUp() {
  fetch(`${API_URL}/api/health/`).catch(() => {})
}

export async function planTrip(payload) {
  let res
  try {
    res = await fetch(`${API_URL}/api/trip/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch {
    throw new Error('Could not reach the server. Check your connection and try again.')
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || 'Something went wrong, try again')
  return data
}
