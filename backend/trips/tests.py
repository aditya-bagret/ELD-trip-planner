from datetime import date

from django.test import SimpleTestCase

from .constants import (
    BREAK_AFTER_DRIVE_MIN, BREAK_MIN, CYCLE_LIMIT_MIN, FUEL_EVERY_MILES,
    MAX_DRIVE_MIN, REST_MIN, RESTART_MIN, WINDOW_MIN,
)
from .hos import simulate
from .logs import build_daily_logs, build_stops

# lat -> name; mid-route stops (dummy locate) sit at lat 0
NAMES = {1.0: "Dallas, TX", 2.0: "Oklahoma City, OK", 3.0: "Chicago, IL", 0.0: "Joplin, MO"}
START = date(2026, 10, 1)


def legs(*miles):
    """Legs at a fixed 50 mph (HOS_ENGINE §8): current -> pickup -> dropoff."""
    locs = [{"name": NAMES[lat], "lat": lat, "lng": 0.0} for lat in (1.0, 2.0, 3.0)]
    return [{"miles": m, "hours": m / 50, "start": locs[i], "end": locs[i + 1]}
            for i, m in enumerate(miles)]


def locate(leg_index, miles_into_leg):
    return (0.0, 0.0)


def t(s):
    """'Day.HH:MM' -> minutes since Day 1 00:00."""
    day, hm = s.split(".")
    h, m = hm.split(":")
    return (int(day) - 1) * 1440 + int(h) * 60 + int(m)


OFF, SB, DR, ON = "off_duty", "sleeper", "driving", "on_duty"


class SimulateTimelineTests(SimpleTestCase):
    def check(self, events, expected):
        got = [(e["status"], e["type"], e["start"], e["end"]) for e in events]
        want = [(s, ty, t(a), t(b)) for s, ty, a, b in expected]
        self.assertEqual(got, want)

    def test_t1_short_trip(self):
        events = simulate(legs(100, 200), 0, locate)
        self.check(events, [
            (OFF, "off_duty", "1.00:00", "1.08:00"),
            (ON, "pre_trip", "1.08:00", "1.08:15"),
            (DR, "drive", "1.08:15", "1.10:15"),
            (ON, "pickup", "1.10:15", "1.11:15"),
            (DR, "drive", "1.11:15", "1.15:15"),
            (ON, "dropoff", "1.15:15", "1.16:15"),
            (ON, "post_trip", "1.16:15", "1.16:30"),
            (OFF, "off_duty", "1.16:30", "2.00:00"),
        ])
        self.assertAlmostEqual(sum(e["miles"] for e in events), 300)

    def test_t2_30_min_break(self):
        events = simulate(legs(50, 500), 0, locate)
        self.check(events, [
            (OFF, "off_duty", "1.00:00", "1.08:00"),
            (ON, "pre_trip", "1.08:00", "1.08:15"),
            (DR, "drive", "1.08:15", "1.09:15"),
            (ON, "pickup", "1.09:15", "1.10:15"),
            (DR, "drive", "1.10:15", "1.18:15"),
            (OFF, "break", "1.18:15", "1.18:45"),
            (DR, "drive", "1.18:45", "1.20:45"),
            (ON, "dropoff", "1.20:45", "1.21:45"),
            (ON, "post_trip", "1.21:45", "1.22:00"),
            (OFF, "off_duty", "1.22:00", "2.00:00"),
        ])
        self.assertEqual(sum(e["type"] == "break" for e in events), 1)

    def test_t3_11_hour_limit_rest(self):
        events = simulate(legs(25, 600), 0, locate)
        self.check(events, [
            (OFF, "off_duty", "1.00:00", "1.08:00"),
            (ON, "pre_trip", "1.08:00", "1.08:15"),
            (DR, "drive", "1.08:15", "1.08:45"),
            (ON, "pickup", "1.08:45", "1.09:45"),
            (DR, "drive", "1.09:45", "1.17:45"),
            (OFF, "break", "1.17:45", "1.18:15"),
            (DR, "drive", "1.18:15", "1.20:45"),
            (ON, "post_trip", "1.20:45", "1.21:00"),
            (SB, "rest", "1.21:00", "2.07:00"),
            (ON, "pre_trip", "2.07:00", "2.07:15"),
            (DR, "drive", "2.07:15", "2.08:45"),
            (ON, "dropoff", "2.08:45", "2.09:45"),
            (ON, "post_trip", "2.09:45", "2.10:00"),
            (OFF, "off_duty", "2.10:00", "3.00:00"),
        ])
        day1 = sum(e["miles"] for e in events if e["start"] < 1440)
        self.assertAlmostEqual(day1, 550)
        self.assertAlmostEqual(sum(e["miles"] for e in events), 625)

    def test_t4_fuel_stop(self):
        events = simulate(legs(0, 1100), 0, locate)
        self.check(events, [
            (OFF, "off_duty", "1.00:00", "1.08:00"),
            (ON, "pre_trip", "1.08:00", "1.08:15"),
            (ON, "pickup", "1.08:15", "1.09:15"),
            (DR, "drive", "1.09:15", "1.17:15"),
            (OFF, "break", "1.17:15", "1.17:45"),
            (DR, "drive", "1.17:45", "1.20:45"),
            (ON, "post_trip", "1.20:45", "1.21:00"),
            (SB, "rest", "1.21:00", "2.07:00"),
            (ON, "pre_trip", "2.07:00", "2.07:15"),
            (DR, "drive", "2.07:15", "2.15:15"),
            (OFF, "break", "2.15:15", "2.15:45"),
            (DR, "drive", "2.15:45", "2.16:45"),
            (ON, "fuel", "2.16:45", "2.17:15"),
            (DR, "drive", "2.17:15", "2.19:15"),
            (ON, "dropoff", "2.19:15", "2.20:15"),
            (ON, "post_trip", "2.20:15", "2.20:30"),
            (OFF, "off_duty", "2.20:30", "3.00:00"),
        ])
        self.assertEqual(sum(e["type"] == "fuel" for e in events), 1)
        before_fuel = sum(e["miles"] for e in events if e["end"] <= t("2.16:45"))
        self.assertAlmostEqual(before_fuel, 1000)

    def test_t5_70_hour_restart(self):
        events = simulate(legs(0, 200), 68, locate)
        self.check(events, [
            (OFF, "off_duty", "1.00:00", "1.08:00"),
            (ON, "pre_trip", "1.08:00", "1.08:15"),
            (ON, "pickup", "1.08:15", "1.09:15"),
            (DR, "drive", "1.09:15", "1.10:00"),
            (ON, "post_trip", "1.10:00", "1.10:15"),
            (OFF, "restart", "1.10:15", "2.20:15"),
            (ON, "pre_trip", "2.20:15", "2.20:30"),
            (DR, "drive", "2.20:30", "2.23:45"),
            (ON, "dropoff", "2.23:45", "3.00:45"),
            (ON, "post_trip", "3.00:45", "3.01:00"),
            (OFF, "off_duty", "3.01:00", "4.00:00"),
        ])
        self.assertAlmostEqual(sum(e["miles"] for e in events), 200)


def sheets_for(miles, cycle):
    """Simulate, fake reverse geocoding of stops, build daily logs."""
    events = simulate(legs(*miles), cycle, locate)
    for e in events:
        if e["status"] != "driving":
            e["location"] = NAMES[e["lat"]]
    return events, build_daily_logs(events, START, cycle, NAMES[1.0])


def totals(sheet):
    tt = sheet["totals"]
    return (tt["off_duty"], tt["sleeper"], tt["driving"], tt["on_duty"])


class DailyLogTests(SimpleTestCase):
    def test_t1_sheet(self):
        _, sheets = sheets_for((100, 200), 0)
        self.assertEqual(len(sheets), 1)
        s = sheets[0]
        self.assertEqual(totals(s), (15.5, 0, 6, 2.5))
        self.assertEqual(s["total_miles"], 300)
        self.assertEqual((s["date"], s["day_number"]), ("2026-10-01", 1))
        self.assertEqual((s["from"], s["to"]), ("Dallas, TX", "Chicago, IL"))
        self.assertEqual(s["on_duty_today"], 8.5)
        self.assertEqual(s["recap"], {"a": 8.5, "b": 61.5, "c": 8.5})
        self.assertEqual(s["remarks"], [
            {"start_min": 0, "end_min": 495, "location": "Dallas, TX",
             "note": "Pre-trip inspection"},
            {"start_min": 615, "end_min": 675, "location": "Oklahoma City, OK",
             "note": "Pickup — loading"},
            {"start_min": 915, "end_min": 1440, "location": "Chicago, IL",
             "note": "Drop-off — unloading, Post-trip inspection"},
        ])

    def test_t2_totals(self):
        events, sheets = sheets_for((50, 500), 0)
        self.assertEqual([totals(s) for s in sheets], [(10.5, 0, 11, 2.5)])
        stops = build_stops(events, START)
        self.assertEqual([s["type"] for s in stops], ["pickup", "break", "dropoff"])
        self.assertEqual(stops[1], {
            "type": "break", "label": "30-min break",
            "location": {"name": "Joplin, MO", "lat": 0.0, "lng": 0.0},
            "start": "2026-10-01T18:15", "end": "2026-10-01T18:45", "duration_hours": 0.5,
        })

    def test_t3_totals_and_miles(self):
        _, sheets = sheets_for((25, 600), 0)
        self.assertEqual([totals(s) for s in sheets], [(8.5, 3, 11, 1.5), (14, 7, 1.5, 1.5)])
        self.assertEqual([s["total_miles"] for s in sheets], [550, 75])
        self.assertEqual([(s["from"], s["to"]) for s in sheets],
                         [("Dallas, TX", "Joplin, MO"), ("Joplin, MO", "Chicago, IL")])
        self.assertEqual(sheets[1]["remarks"][0], {
            "start_min": 0, "end_min": 435, "location": "Joplin, MO",
            "note": "(cont.) 10-hr rest (sleeper), Pre-trip inspection",
        })

    def test_t4_totals(self):
        events, sheets = sheets_for((0, 1100), 0)
        self.assertEqual([totals(s) for s in sheets], [(8.5, 3, 11, 1.5), (4, 7, 11, 2)])
        self.assertEqual([s["type"] for s in build_stops(events, START)].count("fuel"), 1)

    def test_t5_totals_and_recap(self):
        _, sheets = sheets_for((0, 200), 68)
        self.assertEqual([totals(s) for s in sheets],
                         [(21.75, 0, 0.75, 1.5), (20.25, 0, 3.25, 0.5), (23, 0, 0, 1)])
        # cycle resets when the 34-h restart completes (Day 2 20:15)
        self.assertEqual([s["recap"]["a"] for s in sheets], [70.25, 3.75, 4.75])
        self.assertEqual(sheets[0]["recap"]["b"], 0)
        self.assertEqual(sheets[2]["remarks"][0]["note"],
                         "(cont.) Drop-off — unloading, Post-trip inspection")


TRIPS = [((100, 200), 0), ((50, 500), 0), ((25, 600), 0), ((0, 1100), 0), ((0, 200), 68),
         ((100, 2400), 60)]


class InvariantTests(SimpleTestCase):
    def check_hos(self, events, cycle_used_hours):
        """Replay events independently and check no driving breaks a limit."""
        cycle = round(cycle_used_hours * 60)
        shift_start, drive_shift, since_break = None, 0, 0
        nondrive, off, since_fuel = 0, 0, 0.0
        for e in events:
            m = e["end"] - e["start"]
            if e["status"] in ("driving", "on_duty"):
                if shift_start is None:
                    shift_start = e["start"]
                cycle += m
                off = 0
            else:
                off += m
                if off >= REST_MIN:
                    shift_start, drive_shift = None, 0
                if off >= RESTART_MIN:
                    cycle = 0
            if e["status"] == "driving":
                nondrive = 0
                drive_shift += m
                since_break += m
                since_fuel += e["miles"]
                self.assertLessEqual(drive_shift, MAX_DRIVE_MIN)
                self.assertLessEqual(e["end"] - shift_start, WINDOW_MIN)
                self.assertLessEqual(since_break, BREAK_AFTER_DRIVE_MIN)
                self.assertLessEqual(cycle, CYCLE_LIMIT_MIN)
                self.assertLessEqual(since_fuel, FUEL_EVERY_MILES + 1e-6)
            else:
                nondrive += m
                if nondrive >= BREAK_MIN:
                    since_break = 0
            if e["type"] == "fuel":
                since_fuel = 0.0

    def test_invariants(self):
        for miles, cycle in TRIPS:
            with self.subTest(miles=miles, cycle=cycle):
                events, sheets = sheets_for(miles, cycle)
                self.check_hos(events, cycle)
                self.assertAlmostEqual(sum(s["total_miles"] for s in sheets), sum(miles), 0)
                for s in sheets:
                    self.assertEqual(round(sum(s["totals"].values()), 2), 24)
                    segs = s["segments"]
                    self.assertEqual(segs[0]["start_min"], 0)
                    self.assertEqual(segs[-1]["end_min"], 1440)
                    for a, b in zip(segs, segs[1:]):
                        self.assertEqual(a["end_min"], b["start_min"])
                        self.assertNotEqual(a["status"], b["status"])

    def test_long_trip_rests(self):
        events, sheets = sheets_for((100, 2400), 60)
        types = [e["type"] for e in events]
        self.assertGreaterEqual(types.count("fuel"), 2)
        self.assertIn("restart", types)
        self.assertGreater(len(sheets), 3)

    def test_fuel_when_leg_ends_in_fuel_minute(self):
        # 1,000.5 mi: the 1,000-mi mark and the drop-off fall in the same minute; still fuel first
        events, _ = sheets_for((200.5, 800), 0)
        self.check_hos(events, 0)
        self.assertEqual([e["type"] for e in events].count("fuel"), 1)
