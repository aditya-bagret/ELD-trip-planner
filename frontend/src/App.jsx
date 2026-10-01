import { useEffect, useRef, useState } from 'react'
import { planTrip, warmUp } from './api'
import RouteMap from './components/RouteMap'
import StopsList from './components/StopsList'
import TripForm from './components/TripForm'
import TripSummary from './components/TripSummary'

const EMPTY_FORM = { current_location: '', pickup_location: '', dropoff_location: '', current_cycle_used: '' }

function Brand() {
  return (
    <>
      <span className="size-5 rounded-md bg-blue-600" aria-hidden="true" />
      <h1 className="font-semibold text-slate-900">ELD Trip Planner</h1>
    </>
  )
}

export default function App() {
  const [form, setForm] = useState(EMPTY_FORM)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [editing, setEditing] = useState(true)
  const [sheetOpen, setSheetOpen] = useState(false)
  const [showLogs, setShowLogs] = useState(false) // LogsView (Phase 7) reads this
  const [focusStop, setFocusStop] = useState(null)
  const panelBody = useRef(null)

  useEffect(() => { warmUp() }, [])

  async function handleSubmit() {
    setLoading(true)
    setError(null)
    try {
      const data = await planTrip({ ...form, current_cycle_used: Number(form.current_cycle_used) })
      setResult(data)
      setEditing(false)
      setSheetOpen(false)
      setFocusStop(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function selectStop(index) {
    setFocusStop({ index }) // new object each tap, so re-tapping the same stop flies again
    setSheetOpen(false)
  }

  // The timeline and the map both start with the trip origin
  const stops = result
    ? [{ type: 'start', label: 'Start', location: result.locations.current, start: result.summary.start }, ...result.stops]
    : []
  const expanded = editing || sheetOpen // the form is always shown expanded

  // The peek sheet always shows the route header + tiles, not wherever the list was scrolled to
  useEffect(() => {
    if (!expanded) panelBody.current.scrollTop = 0
  }, [expanded])

  return (
    <div className="relative h-dvh w-full overflow-hidden bg-slate-100 text-slate-600">
      <RouteMap result={result} stops={stops} focusStop={focusStop} loading={loading} />

      <div className="absolute left-3 top-[calc(env(safe-area-inset-top)_+_12px)] z-10 flex h-10 items-center gap-2 rounded-full border border-slate-200 bg-white px-4 text-sm shadow-xl shadow-slate-900/10 lg:hidden">
        <Brand />
      </div>

      {/* One panel: bottom sheet below lg, floating side panel at lg+ */}
      <section
        aria-label={editing ? 'Plan a trip' : 'Trip details'}
        className={`absolute inset-x-0 bottom-0 z-10 flex flex-col rounded-t-2xl border border-b-0 border-slate-200 bg-white pb-[env(safe-area-inset-bottom)] shadow-xl shadow-slate-900/10 transition-[max-height] duration-200 ease-out lg:inset-x-auto lg:bottom-4 lg:left-4 lg:top-4 lg:max-h-none lg:w-[400px] lg:rounded-2xl lg:border-b lg:pb-0 ${
          expanded ? 'max-h-[85dvh]' : 'max-h-[calc(224px_+_env(safe-area-inset-bottom))]'
        }`}
      >
        {editing ? (
          <div className="flex h-6 shrink-0 items-center justify-center lg:hidden" aria-hidden="true">
            <span className="h-1.5 w-10 rounded-full bg-slate-300" />
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setSheetOpen(!sheetOpen)}
            aria-expanded={expanded}
            aria-label={expanded ? 'Collapse trip details' : 'Expand trip details'}
            className="flex h-7 w-full shrink-0 items-center justify-center lg:hidden"
          >
            <span className="h-1.5 w-10 rounded-full bg-slate-300" />
          </button>
        )}

        <div className="hidden shrink-0 items-center gap-2 border-b border-slate-200 px-5 py-4 lg:flex">
          <Brand />
        </div>

        <div
          ref={panelBody}
          className={`min-h-0 flex-1 overscroll-contain px-4 pb-4 lg:overflow-y-auto lg:p-5 ${expanded ? 'overflow-y-auto' : 'overflow-hidden'}`}
        >
          {editing ? (
            <>
              {!result && <p className="mb-4">Plan an HOS-compliant trip and get your daily logs.</p>}
              <TripForm form={form} onChange={setForm} onSubmit={handleSubmit} loading={loading} error={error} />
            </>
          ) : (
            <>
              <TripSummary
                result={result}
                onEdit={() => { setEditing(true); setError(null) }}
                onShowLogs={() => setShowLogs(true)}
              />
              <StopsList stops={stops} onSelect={selectStop} />
            </>
          )}
        </div>
      </section>
    </div>
  )
}
