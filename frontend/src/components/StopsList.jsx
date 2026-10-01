import { STOP_COLORS } from '../constants'
import { formatDateTime, formatDuration, formatEnd } from '../format'

function when(stop) {
  if (stop.type === 'start') return formatDateTime(stop.start)
  return `${formatDateTime(stop.start)} – ${formatEnd(stop.start, stop.end)} · ${formatDuration(stop.duration_hours)}`
}

export default function StopsList({ stops, onSelect }) {
  return (
    <section className="mt-5">
      <h3 className="mb-1 text-sm font-semibold text-slate-900">Stops</h3>
      <ol>
        {stops.map((stop, i) => (
          <li key={i} className="relative">
            {i < stops.length - 1 && (
              <span aria-hidden="true" className="absolute -bottom-3.5 left-[14px] top-7 w-0.5 bg-slate-200" />
            )}
            <button
              type="button"
              onClick={() => onSelect(i)}
              className="flex min-h-12 w-full items-start gap-3 rounded-xl px-2 py-2.5 text-left hover:bg-slate-50 active:bg-slate-100"
            >
              <span
                aria-hidden="true"
                className="relative mt-1 size-3.5 shrink-0 rounded-full ring-2 ring-white"
                style={{ backgroundColor: STOP_COLORS[stop.type] }}
              />
              <span className="min-w-0">
                <span className="block text-sm font-semibold text-slate-900">{stop.label}</span>
                <span className="block truncate text-sm text-slate-600">{stop.location.name}</span>
                <span className="block text-xs text-slate-500">{when(stop)}</span>
              </span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  )
}
