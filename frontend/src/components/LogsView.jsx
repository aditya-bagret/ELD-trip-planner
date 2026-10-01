import { useEffect, useRef, useState } from 'react'
import { formatDate, formatDuration } from '../format'
import LogSheet from './LogSheet'

const CHIPS = [
  ['off_duty', 'Off duty', 'bg-slate-100 text-slate-700'],
  ['sleeper', 'Sleeper', 'bg-violet-50 text-violet-700'],
  ['driving', 'Driving', 'bg-blue-50 text-blue-700'],
  ['on_duty', 'On duty', 'bg-amber-50 text-amber-800'],
]

const NAV_BTN = 'h-12 rounded-xl border border-slate-200 bg-white px-4 font-semibold text-slate-900 hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white'

export default function LogsView({ result, onClose }) {
  const [day, setDay] = useState(0)
  const pills = useRef([])
  const { logs, locations } = result
  const sheet = logs[day]

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  // Keep the selected pill visible when Prev / Next moves past the edge of the strip
  useEffect(() => {
    pills.current[day]?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  }, [day])

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Daily logs"
      className="logs-enter fixed inset-0 z-[1000] flex flex-col bg-slate-100 text-slate-600"
    >
      <header className="flex shrink-0 items-center gap-2 border-b border-slate-200 bg-white px-2 pb-2 pt-[calc(env(safe-area-inset-top)_+_8px)]">
        <button
          type="button"
          onClick={onClose}
          aria-label="Back to trip"
          autoFocus
          className="flex size-11 shrink-0 items-center justify-center rounded-full text-slate-900 hover:bg-slate-100"
        >
          <svg viewBox="0 0 24 24" className="size-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <div className="min-w-0">
          <h2 className="font-semibold text-slate-900">Daily logs</h2>
          <p className="truncate text-sm text-slate-500">{locations.current.name} → {locations.dropoff.name}</p>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain pb-[env(safe-area-inset-bottom)]">
        <div className="mx-auto max-w-[1100px] space-y-3 py-3 lg:py-5">
          <div className="flex gap-2 overflow-x-auto px-3 py-1 lg:-mx-1 lg:px-1" role="tablist" aria-label="Log day">
            {logs.map((log, i) => (
              <button
                key={log.date}
                ref={(el) => { pills.current[i] = el }}
                type="button"
                role="tab"
                aria-selected={i === day}
                onClick={() => setDay(i)}
                className={`h-12 shrink-0 rounded-full border px-4 text-sm font-semibold ${
                  i === day ? 'border-blue-600 bg-blue-600 text-white' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                }`}
              >
                Day {log.day_number} · {formatDate(log.date)}
              </button>
            ))}
          </div>

          <section className="mx-3 rounded-2xl border border-slate-200 bg-white p-4 lg:mx-0">
            <div className="flex items-baseline justify-between gap-3">
              <p className="min-w-0 truncate text-sm text-slate-500">{sheet.from} → {sheet.to}</p>
              <p className="shrink-0 font-semibold text-slate-900">{Math.round(sheet.total_miles).toLocaleString()} mi</p>
            </div>
            <ul className="mt-3 flex flex-wrap gap-2">
              {CHIPS.map(([status, label, color]) => (
                <li key={status} className={`rounded-full px-3 py-1 text-sm font-medium ${color}`}>
                  {label} {formatDuration(sheet.totals[status])}
                </li>
              ))}
            </ul>
          </section>

          <p className="px-3 text-xs text-slate-500 lg:hidden">Scroll sideways or rotate your phone to see the full sheet</p>
          <div className="mx-3 overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-900/10 lg:mx-0">
            <div className="min-w-[900px] p-4">
              <LogSheet sheet={sheet} homeTerminal={logs[0].from} />
            </div>
          </div>

          <div className="flex justify-between gap-3 px-3 lg:px-0">
            <button type="button" className={NAV_BTN} disabled={day === 0} onClick={() => setDay(day - 1)}>
              ← Prev day
            </button>
            <button type="button" className={NAV_BTN} disabled={day === logs.length - 1} onClick={() => setDay(day + 1)}>
              Next day →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
