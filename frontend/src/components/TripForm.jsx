import { useState } from 'react'
import Assumptions from './Assumptions'

const LOCATIONS = [
  ['current_location', 'Current location', 'Current location (e.g. Dallas, TX)', 'border-2 border-slate-500 bg-white'],
  ['pickup_location', 'Pickup location', 'Pickup location (e.g. Tulsa, OK)', 'bg-emerald-600'],
  ['dropoff_location', 'Drop-off location', 'Drop-off location (e.g. Chicago, IL)', 'bg-red-600'],
]

const INPUT =
  'h-12 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 text-base text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 aria-[invalid=true]:border-red-400'

function validate(form) {
  const errors = {}
  for (const [name, label] of LOCATIONS) {
    if (!form[name].trim()) errors[name] = `${label} is required`
  }
  const cycle = form.current_cycle_used
  if (cycle.trim() === '') errors.current_cycle_used = 'Cycle hours used is required'
  else if (!(Number(cycle) >= 0 && Number(cycle) <= 70)) errors.current_cycle_used = 'Enter a number from 0 to 70'
  return errors
}

export default function TripForm({ form, onChange, onSubmit, loading, error }) {
  const [errors, setErrors] = useState({})

  function change(name, value) {
    onChange({ ...form, [name]: value })
    if (errors[name]) setErrors({ ...errors, [name]: null })
  }

  function submit(e) {
    e.preventDefault()
    const found = validate(form)
    setErrors(found)
    if (Object.keys(found).length === 0) onSubmit()
  }

  return (
    <form noValidate onSubmit={submit} className="space-y-4">
      <div className="relative space-y-2">
        <span aria-hidden="true" className="absolute bottom-6 left-[7px] top-6 border-l-2 border-dotted border-slate-300" />
        {LOCATIONS.map(([name, label, placeholder, dot]) => (
          <div key={name}>
            <div className="flex items-center gap-3">
              <span aria-hidden="true" className={`relative size-4 shrink-0 rounded-full ${dot}`} />
              <label htmlFor={name} className="sr-only">{label}</label>
              <input
                id={name}
                className={INPUT}
                placeholder={placeholder}
                autoComplete="off"
                value={form[name]}
                onChange={(e) => change(name, e.target.value)}
                aria-invalid={Boolean(errors[name])}
                aria-describedby={errors[name] ? `${name}-error` : undefined}
              />
            </div>
            {errors[name] && <p id={`${name}-error`} className="ml-7 mt-1 text-sm text-red-700">{errors[name]}</p>}
          </div>
        ))}
      </div>

      <div>
        <label htmlFor="current_cycle_used" className="mb-1.5 block text-sm font-medium text-slate-700">Cycle hours used</label>
        <div className="relative">
          <input
            id="current_cycle_used"
            type="number"
            inputMode="decimal"
            step="0.5"
            min="0"
            max="70"
            placeholder="0"
            className={`${INPUT} pr-16 [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none`}
            value={form.current_cycle_used}
            onChange={(e) => change('current_cycle_used', e.target.value)}
            aria-invalid={Boolean(errors.current_cycle_used)}
            aria-describedby={errors.current_cycle_used ? 'current_cycle_used-error' : 'current_cycle_used-hint'}
          />
          <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-slate-500">/ 70 h</span>
        </div>
        {errors.current_cycle_used
          ? <p id="current_cycle_used-error" className="mt-1 text-sm text-red-700">{errors.current_cycle_used}</p>
          : <p id="current_cycle_used-hint" className="mt-1 text-xs text-slate-500">On-duty hours already used in the current 8-day cycle.</p>}
      </div>

      {error && <div role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <div>
        <button
          type="submit"
          disabled={loading}
          className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-blue-600 font-semibold text-white hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 active:scale-[0.98] disabled:cursor-wait disabled:opacity-80"
        >
          {loading && (
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true" className="size-5 animate-spin">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
              <path d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
          )}
          {loading ? 'Planning…' : 'Plan trip'}
        </button>
        {loading && (
          <p className="mt-2 text-center text-xs text-slate-500" aria-live="polite">
            Planning route &amp; HOS schedule… first request can take up to a minute
          </p>
        )}
      </div>

      <Assumptions />
    </form>
  )
}
