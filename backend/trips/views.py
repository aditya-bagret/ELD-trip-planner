import json
import logging
from datetime import date

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import geo, mock_geo
from .hos import simulate
from .logs import build_daily_logs, build_stops, iso

log = logging.getLogger(__name__)

LOCATION_FIELDS = ("current_location", "pickup_location", "dropoff_location")


def health(request):
    return JsonResponse({"ok": True})


def _error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def _validate(body):
    """-> (data, error message)."""
    try:
        data = json.loads(body)
    except ValueError:
        return None, "Request body must be JSON"
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"
    for field in LOCATION_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return None, f"{field} is required"
        data[field] = value.strip()
    cycle = data.get("current_cycle_used")
    if isinstance(cycle, bool) or not isinstance(cycle, (int, float)) or not 0 <= cycle <= 70:
        return None, "current_cycle_used must be a number between 0 and 70"
    return data, None


@csrf_exempt
@require_POST
def plan_trip(request):
    data, message = _validate(request.body)
    if message:
        return _error(message)
    try:
        return JsonResponse(_plan(data))
    except geo.LocationNotFound as e:
        return _error(str(e))
    except geo.GeoServiceError:
        log.exception("ORS request failed")
        return _error("Routing service failed, try again", 502)
    except Exception:
        log.exception("Trip planning failed")
        return _error("Something went wrong planning this trip", 500)


def _plan(data):
    src = mock_geo if settings.MOCK_GEO else geo
    current, pickup, dropoff = (src.geocode(data[f]) for f in LOCATION_FIELDS)
    legs, route_line = src.route([current, pickup, dropoff])
    cycle_used = data["current_cycle_used"]
    events = simulate(legs, cycle_used, geo.make_locate(legs))

    # Stops at the three entered places keep their geocoded names; other stops get reverse-geocoded.
    known = {geo.coord_key(p["lat"], p["lng"]): p["name"] for p in (current, pickup, dropoff)}
    stops = [e for e in events if e["status"] != "driving"]
    names = src.reverse_geocode_many(
        [(e["lat"], e["lng"]) for e in stops if geo.coord_key(e["lat"], e["lng"]) not in known])
    for e in stops:
        key = geo.coord_key(e["lat"], e["lng"])
        e["location"] = known.get(key) or names[key]

    start_date = date.today()
    logs = build_daily_logs(events, start_date, cycle_used, current["name"])
    start = next(e["start"] for e in events if e["type"] == "pre_trip")
    end = next(e["end"] for e in reversed(events) if e["type"] == "post_trip")
    return {
        "summary": {
            "total_miles": round(sum(leg["miles"] for leg in legs), 1),
            "total_driving_hours": round(sum(e["end"] - e["start"] for e in events
                                             if e["status"] == "driving") / 60, 2),
            "total_trip_hours": round((end - start) / 60, 2),
            "start": iso(start_date, start),
            "end": iso(start_date, end),
            "days": len(logs),
        },
        "locations": {"current": current, "pickup": pickup, "dropoff": dropoff},
        "route": route_line,
        "stops": build_stops(events, start_date),
        "logs": logs,
    }
