"""Pure HOS trip simulation (HOS_ENGINE §5). Integer minutes since Day 1 00:00."""
from math import ceil

from .constants import (
    BREAK_AFTER_DRIVE_MIN, BREAK_MIN, CYCLE_LIMIT_MIN, DAY_MIN, DROPOFF_MIN,
    FUEL_EVERY_MILES, FUEL_MIN, MAX_DRIVE_MIN, PICKUP_MIN, POST_TRIP_MIN,
    PRE_TRIP_MIN, REST_MIN, RESTART_MIN, TRIP_START_HOUR, WINDOW_MIN,
)


def _ceil_min(x):
    # ceil that ignores float noise like 120.00000000001
    return ceil(x - 1e-9)


class _Sim:
    def __init__(self, cycle_used_hours, pos):
        self.events = []
        self.t = 0
        self.cycle = round(cycle_used_hours * 60)
        self.shift_start = 0
        self.drive_in_shift = 0
        self.drive_since_break = 0
        self.nondrive_streak = 0
        self.miles_since_fuel = 0.0
        self.pos = pos

    def add(self, status, type_, minutes, miles=0.0, end_pos=None):
        end_pos = end_pos or self.pos
        last = self.events[-1] if self.events else None
        if type_ == "drive" and last and last["type"] == "drive" and last["end"] == self.t:
            last["end"] += minutes
            last["miles"] += miles
            last["end_lat"], last["end_lng"] = end_pos
        else:
            self.events.append({
                "status": status, "type": type_,
                "start": self.t, "end": self.t + minutes, "miles": miles,
                "lat": self.pos[0], "lng": self.pos[1],
                "end_lat": end_pos[0], "end_lng": end_pos[1],
                "location": None,
            })
        self.t += minutes
        self.pos = end_pos
        if status in ("driving", "on_duty"):
            self.cycle += minutes
        if status == "driving":
            self.nondrive_streak = 0
            self.drive_in_shift += minutes
            self.drive_since_break += minutes
        else:
            # 30 consecutive non-driving minutes satisfy the 30-min break (§395.3(a)(3)(ii))
            self.nondrive_streak += minutes
            if self.nondrive_streak >= BREAK_MIN:
                self.drive_since_break = 0

    def start_shift(self):
        # 14-h window starts at the shift's first on-duty minute
        self.shift_start = self.t
        self.drive_in_shift = 0
        self.add("on_duty", "pre_trip", PRE_TRIP_MIN)

    def end_shift(self, rest_type):
        self.add("on_duty", "post_trip", POST_TRIP_MIN)
        if rest_type == "restart":
            # 34 consecutive hours off duty restart the 70-h/8-day cycle
            self.add("off_duty", "restart", RESTART_MIN)
            self.cycle = 0
        else:
            # 10 consecutive hours off resets the 11-h and 14-h limits
            self.add("sleeper", "rest", REST_MIN)
        self.drive_since_break = 0
        self.start_shift()


def simulate(legs, cycle_used_hours, locate):
    start = legs[0]["start"]
    sim = _Sim(cycle_used_hours, (start["lat"], start["lng"]))

    sim.add("off_duty", "off_duty", TRIP_START_HOUR * 60)
    if sim.cycle >= CYCLE_LIMIT_MIN:
        sim.add("off_duty", "restart", RESTART_MIN)
        sim.cycle = 0
    sim.start_shift()

    for i, leg in enumerate(legs):
        remaining = leg["miles"]
        driven = 0.0
        while remaining > 0.01:  # float tolerance: never loop on a tiny residual
            # check order matters: cycle -> 11/14 -> 8-h break -> fuel -> drive
            if sim.cycle >= CYCLE_LIMIT_MIN:  # 70 h / 8 days
                sim.end_shift("restart")
                continue
            if sim.drive_in_shift >= MAX_DRIVE_MIN or sim.t - sim.shift_start >= WINDOW_MIN:  # 11 h / 14 h
                sim.end_shift("rest")
                continue
            if sim.drive_since_break >= BREAK_AFTER_DRIVE_MIN:  # 30 min after 8 h driving
                sim.add("off_duty", "break", BREAK_MIN)
                continue
            if sim.miles_since_fuel >= FUEL_EVERY_MILES:
                sim.add("on_duty", "fuel", FUEL_MIN)
                sim.miles_since_fuel = 0.0
                continue

            mph = leg["miles"] / leg["hours"]
            need = _ceil_min(remaining / mph * 60)
            to_fuel = _ceil_min((FUEL_EVERY_MILES - sim.miles_since_fuel) / mph * 60)
            chunk = min(need, MAX_DRIVE_MIN - sim.drive_in_shift,
                        WINDOW_MIN - (sim.t - sim.shift_start),
                        BREAK_AFTER_DRIVE_MIN - sim.drive_since_break,
                        CYCLE_LIMIT_MIN - sim.cycle, to_fuel)
            assert chunk >= 1, "HOS simulation stalled"
            miles = remaining if chunk == need else min(remaining, chunk * mph / 60)
            to_fuel_miles = FUEL_EVERY_MILES - sim.miles_since_fuel
            # stop at the 1,000-mi mark even when the leg ends in the same (rounded-up) minute
            if chunk == to_fuel and remaining - to_fuel_miles > 0.01:
                miles = to_fuel_miles

            driven += miles
            remaining -= miles
            sim.miles_since_fuel += miles
            sim.add("driving", "drive", chunk, miles, tuple(locate(i, driven)))

        end = leg["end"]
        sim.pos = (end["lat"], end["lng"])
        if i == 0:
            sim.add("on_duty", "pickup", PICKUP_MIN)
        else:
            sim.add("on_duty", "dropoff", DROPOFF_MIN)

    sim.add("on_duty", "post_trip", POST_TRIP_MIN)
    if sim.t % DAY_MIN:
        sim.add("off_duty", "off_duty", DAY_MIN - sim.t % DAY_MIN)  # pad to midnight
    return sim.events
