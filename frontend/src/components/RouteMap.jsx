import { useEffect, useRef, useState } from 'react'
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer, ZoomControl } from 'react-leaflet'
import { STOP_COLORS } from '../constants'
import { formatDateTime, formatDuration, formatEnd } from '../format'

const US_CENTER = [39.5, -98.35]
// CARTO basemaps now need an API key, so standard OSM tiles (free, no key)
const TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
const ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
const BIG = ['start', 'pickup', 'dropoff']

const US_BOUNDS = [[24.5, -124.8], [49.4, -66.9]]

// Padding keeps the bounds clear of the desktop side panel / mobile sheet (DESIGN §2).
// sheetHeight: the peek sheet after a result; the taller form sheet before one.
function fitView(map, bounds, sheetHeight = 240) {
  const desktop = window.matchMedia('(min-width: 1024px)').matches
  map.fitBounds(bounds, desktop
    ? { paddingTopLeft: [440, 40], paddingBottomRight: [40, 40] }
    : { paddingTopLeft: [24, 80], paddingBottomRight: [24, sheetHeight] })
}

function popupTime(stop) {
  if (stop.type === 'start') return formatDateTime(stop.start)
  return `${formatDateTime(stop.start)} → ${formatEnd(stop.start, stop.end)} (${formatDuration(stop.duration_hours)})`
}

export default function RouteMap({ result, stops, focusStop, loading }) {
  const [map, setMap] = useState(null)
  const markers = useRef({})

  useEffect(() => {
    if (!map) return
    if (result) fitView(map, result.route)
    else fitView(map, US_BOUNDS, window.innerHeight * 0.6)
  }, [map, result])

  useEffect(() => {
    if (!map || !focusStop) return
    const { lat, lng } = stops[focusStop.index].location
    const open = () => markers.current[focusStop.index]?.openPopup()
    map.once('moveend', open)
    map.flyTo([lat, lng], 11)
    return () => map.off('moveend', open)
  }, [map, focusStop])

  return (
    <div className="absolute inset-0 z-0">
      <MapContainer ref={setMap} center={US_CENTER} zoom={4} zoomControl={false} className="h-full w-full">
        <TileLayer url={TILES} attribution={ATTRIBUTION} />
        <ZoomControl position="bottomright" />
        {result && (
          <>
            <Polyline positions={result.route} pathOptions={{ color: '#1e40af', weight: 9 }} />
            <Polyline positions={result.route} pathOptions={{ color: '#3b82f6', weight: 5 }} />
            {stops.map((stop, i) => (
              <CircleMarker
                key={i}
                ref={(el) => { markers.current[i] = el }}
                center={[stop.location.lat, stop.location.lng]}
                radius={BIG.includes(stop.type) ? 11 : 8}
                pathOptions={{ color: '#fff', weight: 3, fillColor: STOP_COLORS[stop.type], fillOpacity: 1 }}
              >
                <Popup>
                  <div className="font-semibold text-slate-900">{stop.label}</div>
                  <div className="text-slate-600">{stop.location.name}</div>
                  <div className="text-slate-500">{popupTime(stop)}</div>
                </Popup>
              </CircleMarker>
            ))}
          </>
        )}
      </MapContainer>

      {result && (
        <button
          type="button"
          aria-label="Fit route on map"
          onClick={() => fitView(map, result.route)}
          className="absolute bottom-[calc(254px_+_env(safe-area-inset-bottom))] right-3 z-[1000] flex size-11 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 shadow-xl shadow-slate-900/10 hover:bg-slate-50 lg:bottom-[100px] lg:right-2.5"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true" className="size-5">
            <circle cx="12" cy="12" r="7" />
            <circle cx="12" cy="12" r="2.5" fill="currentColor" />
            <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
          </svg>
        </button>
      )}

      {loading && (
        <div className="absolute inset-x-0 top-0 z-[1000] h-1 overflow-hidden bg-blue-100" role="progressbar" aria-label="Planning trip">
          <div className="progress-bar h-full w-1/3 bg-blue-600" />
        </div>
      )}
    </div>
  )
}
