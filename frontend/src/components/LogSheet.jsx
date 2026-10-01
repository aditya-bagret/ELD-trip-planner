import { SHEET } from '../constants'

// Geometry (DESIGN §5): 24 h across x 110–890, 4 rows × 45 px from y 200
const GRID_LEFT = 110
const GRID_RIGHT = 890
const GRID_TOP = 200
const ROW_H = 45
const GRID_BOTTOM = GRID_TOP + 4 * ROW_H
const ROWS = ['off_duty', 'sleeper', 'driving', 'on_duty']
const ROW_LABELS = [['1. Off Duty'], ['2. Sleeper Berth'], ['3. Driving'], ['4. On Duty', '(not driving)']]

const x = (min) => GRID_LEFT + (min * (GRID_RIGHT - GRID_LEFT)) / 1440
const rowY = (status) => GRID_TOP + ROW_H / 2 + ROWS.indexOf(status) * ROW_H

const INK = '#1d4ed8' // blue-700, the "hand-filled" values
const LINE = '#0f172a'
const FLAG_BOTTOM = 415

const HOUR_LABELS = Array.from({ length: 25 }, (_, h) =>
  h === 0 || h === 24 ? null : h === 12 ? 'Noon' : String(h % 12))

// Hour lines full height; 30-min ticks half and 15-min ticks a quarter, hanging from each row's top edge
function gridPath() {
  let d = ''
  for (let q = 0; q <= 96; q++) {
    const px = x(q * 15)
    if (q % 4 === 0) {
      d += `M${px} ${GRID_TOP}V${GRID_BOTTOM}`
      continue
    }
    const len = q % 2 === 0 ? ROW_H / 2 : ROW_H / 4
    for (let r = 0; r < 4; r++) d += `M${px} ${GRID_TOP + r * ROW_H}v${len}`
  }
  return d
}
const GRID_PATH = gridPath()

// Labels run down-right at 45°: shorten them so ones near midnight stay inside the viewBox (≈4 px of x per char)
function remarkLabel(text, px) {
  const max = Math.min(32, Math.floor((990 - px) / 4))
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

function Field({ x1, x2, y, value, caption, center }) {
  const vx = center ? (x1 + x2) / 2 : x1 + 4
  return (
    <g>
      <line x1={x1} x2={x2} y1={y} y2={y} stroke={LINE} />
      {value && <text x={vx} y={y - 5} fontSize="13" fill={INK} textAnchor={center ? 'middle' : 'start'}>{value}</text>}
      {caption && <text x={(x1 + x2) / 2} y={y + 11} fontSize="10" textAnchor="middle">{caption}</text>}
    </g>
  )
}

function Box({ x1, value, caption }) {
  return (
    <g>
      <rect x={x1} y={82} width={150} height={36} fill="none" stroke={LINE} />
      <text x={x1 + 75} y={105} fontSize="13" fill={INK} textAnchor="middle">{value}</text>
      <text x={x1 + 75} y={130} fontSize="10" textAnchor="middle">{caption}</text>
    </g>
  )
}

function Lines({ x: lx, y, lines, size = 10, ...props }) {
  return lines.map((line, i) => (
    <text key={i} x={lx} y={y + i * (size + 3)} fontSize={size} {...props}>{line}</text>
  ))
}

export default function LogSheet({ sheet, homeTerminal }) {
  const [year, month, day] = sheet.date.split('-')
  const points = sheet.segments
    .flatMap((s) => [`${x(s.start_min)},${rowY(s.status)}`, `${x(s.end_min)},${rowY(s.status)}`])
    .join(' ')
  const miles = Math.round(sheet.total_miles).toLocaleString()
  const recap = [
    ['', sheet.on_duty_today, ['On duty hours today,', 'total lines 3 & 4']],
    ['A.', sheet.recap.a, ['Total hours on duty', 'last 7 days', 'including today']],
    ['B.', sheet.recap.b, ['Total hours available', 'tomorrow', '70 hr minus A*']],
    ['C.', sheet.recap.c, ['Total hours on duty', 'last 8 days', 'including today']],
  ]

  return (
    <svg
      viewBox="0 0 1000 720"
      className="w-full"
      role="img"
      aria-label={`Daily log for ${month}/${day}/${year}`}
      fontFamily="Inter, system-ui, sans-serif"
      fill={LINE}
    >
      <rect width="1000" height="720" fill="white" />

      {/* Header */}
      <text x="0" y="22" fontSize="22" fontWeight="700">Drivers Daily Log</text>
      <text x="44" y="38" fontSize="11">(24 hours)</text>
      {[[300, month, '(month)'], [390, day, '(day)'], [480, year, '(year)']].map(([fx, value, caption], i) => (
        <g key={caption}>
          <Field x1={fx} x2={fx + 70} y={22} value={value} caption={caption} center />
          {i < 2 && <text x={fx + 80} y={20} fontSize="16">/</text>}
        </g>
      ))}
      <Lines x={640} y={14} lines={['Original - File at home terminal.', 'Duplicate - Driver retains in his/her possession for 8 days.']} />

      <text x="0" y="68" fontSize="13" fontWeight="600">From:</text>
      <Field x1={42} x2={450} y={68} value={sheet.from} />
      <text x="500" y="68" fontSize="13" fontWeight="600">To:</text>
      <Field x1={526} x2={1000} y={68} value={sheet.to} />

      <Box x1={0} value={miles} caption="Total Miles Driving Today" />
      <Box x1={165} value={miles} caption="Total Mileage Today" />
      <Field x1={0} x2={315} y={152} value={SHEET.truck} caption="Truck/Tractor and Trailer Numbers or License Plate(s)/State" />

      <Field x1={400} x2={1000} y={96} value={SHEET.carrier} caption="Name of Carrier or Carriers" />
      <Field x1={400} x2={1000} y={126} value={SHEET.mainOffice} caption="Main Office Address" />
      <Field x1={400} x2={1000} y={156} value={homeTerminal} caption="Home Terminal Address" />

      {/* Hour band */}
      <rect x="70" y="180" width="930" height="20" />
      {[GRID_LEFT, GRID_RIGHT].map((mx) => (
        <text key={mx} x={mx} y="188" fontSize="8" fill="white" textAnchor="middle">
          <tspan x={mx}>Mid-</tspan>
          <tspan x={mx} dy="9">night</tspan>
        </text>
      ))}
      {HOUR_LABELS.map((label, h) => label && (
        <text key={h} x={x(h * 60)} y="194" fontSize="10" fontWeight="600" fill="white" textAnchor="middle">{label}</text>
      ))}
      <text x="950" y="194" fontSize="10" fill="white" textAnchor="middle">Total Hours</text>

      {/* Grid */}
      {ROW_LABELS.map((lines, r) => (
        <Lines key={r} x={0} y={rowY(ROWS[r]) + (lines.length > 1 ? -2 : 4)} lines={lines} size={11} fontWeight="600" />
      ))}
      <rect x={GRID_LEFT} y={GRID_TOP} width={GRID_RIGHT - GRID_LEFT} height={4 * ROW_H} fill="none" stroke={LINE} />
      {[1, 2, 3].map((r) => (
        <line key={r} x1={GRID_LEFT} x2={GRID_RIGHT} y1={GRID_TOP + r * ROW_H} y2={GRID_TOP + r * ROW_H} stroke={LINE} />
      ))}
      <path d={GRID_PATH} stroke={LINE} strokeWidth="0.75" fill="none" />

      {/* Totals */}
      {ROWS.map((status) => (
        <g key={status}>
          <text x="950" y={rowY(status) + 5} fontSize="13" fill={INK} textAnchor="middle">{sheet.totals[status].toFixed(2)}</text>
          <line x1="910" x2="990" y1={rowY(status) + 10} y2={rowY(status) + 10} stroke={LINE} />
        </g>
      ))}
      <line x1="910" x2="990" y1="384" y2="384" stroke={LINE} strokeWidth="1.5" />
      <text x="950" y="400" fontSize="13" fontWeight="600" fill={INK} textAnchor="middle">
        {ROWS.reduce((sum, s) => sum + sheet.totals[s], 0).toFixed(2)}
      </text>

      {/* Duty-status line */}
      <polyline points={points} fill="none" stroke={INK} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

      {/* Remarks: bracket under the grid for stops ≥ 30 min, a flag at each stop, label running down-right */}
      <text x="0" y="420" fontSize="13" fontWeight="700">Remarks</text>
      {sheet.remarks.map((r, i) => {
        const x1 = x(r.start_min)
        const text = `${r.location} — ${r.note}`
        return (
          <g key={i}>
            {r.end_min - r.start_min >= 30 && (
              <path d={`M${x1} 383V389H${x(r.end_min)}V383`} fill="none" stroke={LINE} />
            )}
            <line x1={x1} x2={x1} y1={GRID_BOTTOM} y2={FLAG_BOTTOM} stroke={LINE} />
            <text x={x1 + 3} y={FLAG_BOTTOM + 3} fontSize="10" transform={`rotate(45 ${x1} ${FLAG_BOTTOM})`}>
              <title>{text}</title>
              {remarkLabel(text, x1)}
            </text>
          </g>
        )
      })}
      <line x1="1" x2="1" y1="428" y2="594" stroke={LINE} strokeWidth="2.5" />
      <line x1="0" x2="1000" y1="594" y2="594" stroke={LINE} />

      {/* Shipping documents */}
      <Lines x={8} y={462} lines={['Shipping', 'Documents:']} size={11} fontWeight="700" />
      <Field x1={8} x2={150} y={506} value={`Load #${year}${month}${day}-01`} caption="DVL or Manifest No." />
      <Field x1={8} x2={150} y={546} value={SHEET.commodity} caption="Shipper & Commodity" />

      <text x="560" y="568" fontSize="10" fill="#64748b" textAnchor="middle">
        Enter name of place you reported and where released from work and when and where each change of duty occurred.
      </text>
      <text x="560" y="582" fontSize="10" fill="#64748b" textAnchor="middle">Use time standard of home terminal.</text>

      {/* Recap (70 hr / 8 day) */}
      <Lines x={0} y={618} lines={['Recap:', 'Complete at', 'end of day']} size={11} fontWeight="700" />
      <Lines x={105} y={618} lines={['70 Hour /', '8 Day', 'Drivers']} size={11} fontWeight="700" />
      {recap.map(([letter, value, lines], i) => {
        const cx = 200 + i * 180
        return (
          <g key={i}>
            {letter && <text x={cx} y={622} fontSize="14" fontWeight="700">{letter}</text>}
            <Field x1={cx + 22} x2={cx + 150} y={624} value={value.toFixed(2)} center />
            <Lines x={cx} y={644} lines={lines} />
          </g>
        )
      })}
      <Lines x={905} y={618} lines={['*If you took 34', 'consecutive hours', 'off duty you have', '60/70 hours', 'available.']} />
    </svg>
  )
}
