"""HOS rule values and trip assumptions (HOS_ENGINE §2). All times in minutes."""

TRIP_START_HOUR = 8              # trip starts 08:00 on today's date; 00:00–08:00 Day 1 is off duty
PRE_TRIP_MIN = 15                # on duty, start of every shift
POST_TRIP_MIN = 15               # on duty, end of every shift and end of trip
PICKUP_MIN = 60
DROPOFF_MIN = 60
FUEL_MIN = 30                    # on duty
BREAK_MIN = 30                   # off duty
REST_MIN = 600                   # 10 h, logged on Sleeper Berth line
RESTART_MIN = 2040               # 34 h, logged on Off Duty line
MAX_DRIVE_MIN = 660              # 11 h
WINDOW_MIN = 840                 # 14 h
BREAK_AFTER_DRIVE_MIN = 480      # 8 h
CYCLE_LIMIT_MIN = 4200           # 70 h
FUEL_EVERY_MILES = 1000

DAY_MIN = 1440
