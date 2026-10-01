"""Offline stand-in for geo.py (MOCK_GEO=True): same geocode / route / reverse_geocode_many,
served from mock_data.json, which holds ORS driving-hgv legs between a fixed set of demo cities
and reverse-geocoded place names along them. For demos when the ORS quota is used up."""
import json
import re
from pathlib import Path

from .geo import LocationNotFound, _haversine, coord_key

DATA = json.loads((Path(__file__).parent / "mock_data.json").read_text())
ALIASES = {"nyc": "New York, NY", "new york city": "New York, NY", "la": "Los Angeles, CA",
           "okc": "Oklahoma City, OK", "kc": "Kansas City, MO", "saint louis": "St. Louis, MO",
           "st louis": "St. Louis, MO"}


def _norm(text):
    return re.sub(r"[^a-z ]", "", text.lower()).strip()


def _lookup():
    table = {_norm(k): v for k, v in ALIASES.items()}
    for name in DATA["cities"]:
        table[_norm(name)] = name                          # "chicago il"
        table[_norm(name.split(",")[0])] = name            # "chicago"
    return table


LOOKUP = _lookup()


def geocode(text):
    name = LOOKUP.get(re.sub(r"\s+", " ", _norm(text)))
    if not name:
        raise LocationNotFound(f"Demo mode only knows: {', '.join(sorted(DATA['cities']))}")
    lat, lng = DATA["cities"][name]
    return {"name": name, "lat": lat, "lng": lng}


def _leg(a, b):
    if a["name"] == b["name"]:
        return {"miles": 0, "hours": 0, "geometry": [(a["lat"], a["lng"])]}
    key = "|".join(sorted((a["name"], b["name"])))
    leg = DATA["legs"][key]
    geometry = [tuple(p) for p in leg["geometry"]]
    if key.startswith(b["name"] + "|"):
        geometry.reverse()
    return {"miles": leg["miles"], "hours": leg["hours"], "geometry": geometry}


def route(points):
    """Same shape as geo.route(): (legs, [[lat, lng]] route line)."""
    legs = [{**_leg(a, b), "start": a, "end": b} for a, b in zip(points, points[1:])]
    line = [list(p) for p in legs[0]["geometry"]]
    for leg in legs[1:]:
        line += [list(p) for p in leg["geometry"][1:]]
    return legs, line


def reverse_geocode_many(coords):
    """Name each point after the nearest recorded place."""
    return {coord_key(lat, lng): min(DATA["places"], key=lambda p: _haversine((lat, lng), p[:2]))[2]
            for lat, lng in coords}
