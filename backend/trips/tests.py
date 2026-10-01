from django.test import SimpleTestCase

from .hos import simulate


def legs(*miles):
    """Legs at a fixed 50 mph (HOS_ENGINE §8)."""
    loc = {"name": "X", "lat": 0.0, "lng": 0.0}
    return [{"miles": m, "hours": m / 50, "start": loc, "end": loc} for m in miles]


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
