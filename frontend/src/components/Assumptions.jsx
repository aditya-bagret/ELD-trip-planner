const ITEMS = [
  'The trip starts at 08:00 today; Day 1 before that is off duty.',
  '15-min pre-trip inspection at the start and 15-min post-trip at the end of every shift.',
  '1 hour on duty for pickup and 1 hour for drop-off.',
  'A 30-min fuel stop (on duty) at least every 1,000 miles.',
  '30-min break after 8 h of driving; a fuel stop, pickup or drop-off of 30+ min counts as the break.',
  '11 h driving and a 14 h window per shift; 10-h rests are logged in the sleeper berth.',
  '70 h / 8-day cycle; a 34-h restart (off duty) is taken when the cycle runs out.',
  'One home-terminal clock: no time zones, each log day runs midnight to midnight.',
  'Driving speed per leg = route distance ÷ route time from the routing service.',
  'Cycle hours used are treated as already in the 8-day window; none roll off during the trip.',
]

export default function Assumptions() {
  return (
    <details className="group rounded-xl border border-slate-200 bg-slate-50">
      <summary className="flex h-12 cursor-pointer list-none items-center justify-between rounded-xl px-4 text-sm font-medium text-slate-700 [&::-webkit-details-marker]:hidden">
        Planning assumptions
        <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" className="size-5 text-slate-500 transition-transform group-open:rotate-180">
          <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 11.17l3.71-3.94a.75.75 0 1 1 1.08 1.04l-4.25 4.5a.75.75 0 0 1-1.08 0l-4.25-4.5a.75.75 0 0 1 .02-1.06Z" clipRule="evenodd" />
        </svg>
      </summary>
      <ul className="list-disc space-y-1.5 pb-4 pl-8 pr-4 text-sm text-slate-600">
        {ITEMS.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </details>
  )
}
