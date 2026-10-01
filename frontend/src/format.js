const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// "2026-10-01" → "Oct 1" (no Date parsing, so no time-zone shifts)
export function formatDate(date) {
  const [, month, day] = date.split('-')
  return `${MONTHS[month - 1]} ${Number(day)}`
}

// Naive ISO "2026-10-01T08:15" → "Oct 1, 08:15"
export function formatDateTime(iso) {
  const [date, time] = iso.split('T')
  return `${formatDate(date)}, ${time}`
}

// End of a span: just the time when it's on the same day as the start
export function formatEnd(start, end) {
  return start.slice(0, 10) === end.slice(0, 10) ? end.slice(11) : formatDateTime(end)
}

// 17.5 → "17h 30m"; with days: 33.25 → "1d 9h 15m"
export function formatDuration(hours, withDays = false) {
  let mins = Math.round(hours * 60)
  const parts = []
  if (withDays && mins >= 1440) {
    parts.push(`${Math.floor(mins / 1440)}d`)
    mins %= 1440
  }
  if (mins >= 60) parts.push(`${Math.floor(mins / 60)}h`)
  if (mins % 60) parts.push(`${mins % 60}m`)
  return parts.join(' ') || '0m'
}
