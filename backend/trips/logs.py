"""Pure daily-log + map-stop building from simulated events (HOS_ENGINE §6–§7)."""
from datetime import datetime, time, timedelta

from .constants import CYCLE_LIMIT_MIN, DAY_MIN

STATUSES = ("off_duty", "sleeper", "driving", "on_duty")

NOTES = {
    "pre_trip": "Pre-trip inspection",
    "post_trip": "Post-trip inspection",
    "pickup": "Pickup — loading",
    "dropoff": "Drop-off — unloading",
    "fuel": "Fuel stop",
    "break": "30-min break",
    "rest": "10-hr rest (sleeper)",
    "restart": "34-hr restart",
    "off_duty": "Off duty",
}

STOP_LABELS = {
    "pickup": "Pickup",
    "dropoff": "Drop-off",
    "fuel": "Fuel stop",
    "break": "30-min break",
    "rest": "10-hr rest",
    "restart": "34-hr restart",
}


def iso(start_date, minutes):
    """Minutes since Day 1 00:00 -> 'YYYY-MM-DDTHH:MM' (naive home-terminal time)."""
    dt = datetime.combine(start_date, time()) + timedelta(minutes=minutes)
    return dt.strftime("%Y-%m-%dT%H:%M")


def _hours(minutes):
    return round(minutes / 60, 2)


def _totals(minutes_by_status):
    # Round to 0.01 h with largest remainder so the four totals still add to exactly 24.00.
    hundredths = {s: m * 5 // 3 for s, m in minutes_by_status.items()}  # m / 60 * 100
    short = 2400 - sum(hundredths.values())
    for s in sorted(STATUSES, key=lambda s: -(minutes_by_status[s] * 5 % 3))[:short]:
        hundredths[s] += 1
    return {s: hundredths[s] / 100 for s in STATUSES}


def _pieces(events, from_name):
    """Split events at every midnight; tag each piece with its stop name and stop-run start."""
    name, run_start = from_name, None
    pieces = []
    for e in events:
        if e["status"] == "driving":
            run_start = None  # driving keeps the last stop's name (never reverse-geocoded)
        else:
            name = e["location"] or name
            if run_start is None:
                run_start = e["start"]
        s = e["start"]
        while s < e["end"]:
            cut = min(e["end"], (s // DAY_MIN + 1) * DAY_MIN)
            pieces.append({
                **e, "start": s, "end": cut, "event_end": e["end"],
                "miles": e["miles"] * (cut - s) / (e["end"] - e["start"]),  # pro-rated
                "name": name, "run_start": run_start,
            })
            s = cut
    return pieces


def _remarks(day_pieces, day_start):
    remarks = []
    for p in day_pieces:
        if p["status"] == "driving":
            continue
        last = remarks[-1] if remarks else None
        if last and last["_run"] == p["run_start"]:
            last["end_min"] = p["end"] - day_start
            last["_types"].append(p["type"])
        else:
            remarks.append({"_run": p["run_start"], "_types": [p["type"]],
                            "start_min": p["start"] - day_start, "end_min": p["end"] - day_start,
                            "location": p["name"]})
    for r in remarks:
        notes = list(dict.fromkeys(NOTES[t] for t in r.pop("_types")))
        if len(notes) > 1 and NOTES["off_duty"] in notes:
            notes.remove(NOTES["off_duty"])
        r["note"] = ("(cont.) " if r.pop("_run") < day_start else "") + ", ".join(notes)
    return remarks


def build_daily_logs(events, start_date, cycle_used_hours, from_name):
    pieces = _pieces(events, from_name)
    cycle = round(cycle_used_hours * 60)
    sheets = []
    for d in range(pieces[-1]["start"] // DAY_MIN + 1):
        day_start = d * DAY_MIN
        day = [p for p in pieces if p["start"] // DAY_MIN == d]

        segments, minutes = [], dict.fromkeys(STATUSES, 0)
        for p in day:
            minutes[p["status"]] += p["end"] - p["start"]
            if segments and segments[-1]["status"] == p["status"]:
                segments[-1]["end_min"] = p["end"] - day_start
            else:
                segments.append({"status": p["status"], "start_min": p["start"] - day_start,
                                 "end_min": p["end"] - day_start})
            if p["status"] in ("driving", "on_duty"):
                cycle += p["end"] - p["start"]
            if p["type"] == "restart" and p["end"] == p["event_end"]:
                cycle = 0  # 34-h restart complete: only on-duty time after it counts
        assert sum(minutes.values()) == DAY_MIN, f"day {d + 1} does not total 24 h"
        assert segments[0]["start_min"] == 0 and segments[-1]["end_min"] == DAY_MIN

        totals = _totals(minutes)
        sheets.append({
            "date": (start_date + timedelta(days=d)).isoformat(),
            "day_number": d + 1,
            "from": from_name if d == 0 else day[0]["name"],
            "to": day[-1]["name"],
            "total_miles": round(sum(p["miles"] for p in day), 1),
            "segments": segments,
            "totals": totals,
            "on_duty_today": round(totals["driving"] + totals["on_duty"], 2),
            # 70 h / 8 days recap; no per-day history, so nothing rolls off (a == c)
            "recap": {"a": _hours(cycle), "b": _hours(max(0, CYCLE_LIMIT_MIN - cycle)),
                      "c": _hours(cycle)},
            "remarks": _remarks(day, day_start),
        })
    return sheets


def build_stops(events, start_date):
    return [{
        "type": e["type"],
        "label": STOP_LABELS[e["type"]],
        "location": {"name": e["location"], "lat": e["lat"], "lng": e["lng"]},
        "start": iso(start_date, e["start"]),
        "end": iso(start_date, e["end"]),
        "duration_hours": _hours(e["end"] - e["start"]),
    } for e in events if e["type"] in STOP_LABELS]
