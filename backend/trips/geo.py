"""OpenRouteService client: geocode, route, reverse geocode (TECH_SPEC §4)."""
from bisect import bisect_left
from concurrent.futures import ThreadPoolExecutor
from math import asin, ceil, cos, radians, sin, sqrt

import requests
from django.conf import settings

BASE = "https://api.openrouteservice.org"
TIMEOUT = 20
METERS_PER_MILE = 1609.344
EARTH_MILES = 3958.8
MAX_ROUTE_POINTS = 1500


class LocationNotFound(Exception):
    pass


class GeoServiceError(Exception):
    pass


def _get(path, params):
    try:
        r = requests.get(BASE + path, params=params, timeout=TIMEOUT,
                         headers={"Authorization": settings.ORS_API_KEY})
        r.raise_for_status()
        return r.json()
    except (requests.RequestException, ValueError) as e:
        raise GeoServiceError(str(e)) from e


def _place_name(props):
    city = props.get("locality") or props.get("name")
    return f"{city}, {props['region_a']}" if props.get("region_a") else city


def coord_key(lat, lng):
    return (round(lat, 3), round(lng, 3))


def geocode(text):
    data = _get("/geocode/search", {"text": text, "size": 1, "boundary.country": "US"})
    if not data.get("features"):
        raise LocationNotFound(f"Could not find location: {text}")
    f = data["features"][0]
    lng, lat = f["geometry"]["coordinates"]
    return {"name": _place_name(f["properties"]), "lat": lat, "lng": lng}


def _reverse_geocode(lat, lng):
    try:
        data = _get("/geocode/reverse", {"point.lon": lng, "point.lat": lat,
                                         "size": 1, "layers": "locality,localadmin,county"})
        return _place_name(data["features"][0]["properties"])
    except (GeoServiceError, IndexError, KeyError):
        return f"{lat:.3f}, {lng:.3f}"


def reverse_geocode_many(coords):
    """[(lat, lng)] -> {coord_key: "City, ST"}; deduped, 5 requests in parallel."""
    unique = {coord_key(lat, lng): (lat, lng) for lat, lng in coords}
    with ThreadPoolExecutor(max_workers=5) as pool:
        names = pool.map(lambda c: _reverse_geocode(*c), unique.values())
    return dict(zip(unique, names))


def _directions(profile, points):
    try:
        r = requests.post(f"{BASE}/v2/directions/{profile}/geojson", timeout=TIMEOUT,
                          headers={"Authorization": settings.ORS_API_KEY},
                          # radiuses -1: snap city centroids to the nearest road (default 350 m fails)
                          json={"coordinates": [[p["lng"], p["lat"]] for p in points],
                                "radiuses": [-1] * len(points)})
        r.raise_for_status()
        return r.json()["features"][0]
    except (requests.RequestException, ValueError, KeyError, IndexError) as e:
        raise GeoServiceError(str(e)) from e


def route(points):
    """points = [current, pickup, dropoff] locs -> (legs, downsampled [[lat, lng]] route)."""
    try:
        feature = _directions("driving-hgv", points)
    except GeoServiceError:
        feature = _directions("driving-car", points)

    coords = [(lat, lng) for lng, lat, *_ in feature["geometry"]["coordinates"]]
    way_points = feature["properties"]["way_points"]
    segments = feature["properties"]["segments"]
    legs = []
    for i in range(len(points) - 1):
        seg = segments[i] if i < len(segments) else {}  # ORS may omit a zero-length leg
        legs.append({
            "miles": seg.get("distance", 0) / METERS_PER_MILE,
            "hours": seg.get("duration", 0) / 3600,
            "start": points[i],
            "end": points[i + 1],
            "geometry": coords[way_points[i]:way_points[i + 1] + 1],
        })

    step = ceil(len(coords) / MAX_ROUTE_POINTS)
    line = coords[::step]
    if line[-1] != coords[-1]:
        line.append(coords[-1])
    return legs, [list(p) for p in line]


def _haversine(a, b):
    lat1, lng1, lat2, lng2 = map(radians, (*a, *b))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return 2 * EARTH_MILES * asin(sqrt(h))


def make_locate(legs):
    """locate(leg_index, miles_into_leg) -> (lat, lng) along the full-resolution leg geometry."""
    tables = []
    for leg in legs:
        pts = leg["geometry"] or [(leg["start"]["lat"], leg["start"]["lng"])]
        cum = [0.0]
        for a, b in zip(pts, pts[1:]):
            cum.append(cum[-1] + _haversine(a, b))
        # scale geometry length to ORS's road distance so miles line up with the simulation
        scale = leg["miles"] / cum[-1] if cum[-1] else 0
        tables.append((pts, [c * scale for c in cum]))

    def locate(i, miles):
        pts, cum = tables[i]
        j = bisect_left(cum, miles)
        if j == 0:
            return pts[0]
        if j >= len(cum):
            return pts[-1]
        f = (miles - cum[j - 1]) / (cum[j] - cum[j - 1])
        (lat1, lng1), (lat2, lng2) = pts[j - 1], pts[j]
        return (lat1 + f * (lat2 - lat1), lng1 + f * (lng2 - lng1))

    return locate
