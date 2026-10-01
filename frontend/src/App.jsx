export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-600">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[1200px] items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2">
            <span className="h-5 w-5 rounded bg-blue-700" aria-hidden="true" />
            <h1 className="text-lg font-semibold text-slate-900">ELD Trip Planner</h1>
          </div>
          <p className="hidden text-sm text-slate-500 sm:block">HOS-compliant route &amp; daily logs</p>
        </div>
      </header>

      <main className="mx-auto max-w-[1200px] px-4 py-6">
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-500">
          Enter a trip to see the route and generated log sheets.
        </div>
      </main>
    </div>
  )
}
