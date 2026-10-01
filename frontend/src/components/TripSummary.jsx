import { formatDuration } from '../format'

export default function TripSummary({ result, onEdit, onShowLogs }) {
  const { summary, locations } = result
  const tiles = [
    ['Total miles', `${Math.round(summary.total_miles).toLocaleString()} mi`],
    ['Driving', formatDuration(summary.total_driving_hours)],
    ['Trip time', formatDuration(summary.total_trip_hours, true)],
    ['Log days', summary.days],
  ]

  return (
    <div>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="truncate font-semibold text-slate-900">
            {locations.current.name} → {locations.dropoff.name}
          </h2>
          <p className="truncate text-sm text-slate-500">via {locations.pickup.name}</p>
        </div>
        <button
          type="button"
          onClick={onEdit}
          className="-mr-2 -mt-2 h-11 shrink-0 rounded-xl px-3 text-sm font-semibold text-blue-600 hover:bg-blue-50"
        >
          Edit
        </button>
      </div>

      <dl className="mt-3 grid grid-cols-2 gap-2">
        {tiles.map(([label, value]) => (
          <div key={label} className="rounded-xl bg-slate-50 px-3 py-2">
            <dt className="text-xs text-slate-500">{label}</dt>
            <dd className="text-lg font-semibold text-slate-900">{value}</dd>
          </div>
        ))}
      </dl>

      <button
        type="button"
        onClick={onShowLogs}
        className="mt-4 h-12 w-full rounded-xl bg-blue-600 font-semibold text-white hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 active:scale-[0.98]"
      >
        View daily logs ({summary.days})
      </button>
    </div>
  )
}
