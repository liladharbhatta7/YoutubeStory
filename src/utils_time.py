import datetime
import pytz

# Constants
NPT_TIMEZONE = pytz.timezone('Asia/Kathmandu')
UTC_TIMEZONE = pytz.utc

def get_current_npt_time():
    """Returns current time in NPT."""
    return datetime.datetime.now(NPT_TIMEZONE)

def get_npt_time_today(hour, minute, second=0):
    """Returns a datetime object for today at specific NPT time."""
    now = get_current_npt_time()
    return now.replace(hour=hour, minute=minute, second=second, microsecond=0)

def npt_to_utc_iso(npt_dt):
    """Converts NPT datetime to UTC ISO 8601 string for YouTube API."""
    utc_dt = npt_dt.astimezone(UTC_TIMEZONE)
    # YouTube expects: 2023-01-20T19:30:00.000Z
    return utc_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

def validate_schedule_time(npt_dt):
    """
    Ensures the schedule time is in the future. 
    YouTube requires scheduled publish time to be at least 15 mins in future.
    """
    now = get_current_npt_time()
    if npt_dt <= now:
        # If the time has passed, push to 20 mins from current time to avoid API error
        return now + datetime.timedelta(minutes=20)
    return npt_dt

def get_three_daily_schedules():
    """
    NEW: Generates 3 specific UTC ISO strings based on the Nepal Weekly Cycle.
    Sunday-Thursday: Afternoon stress, Evening chill, Late night deep emotion.
    Friday: Early weekend release.
    Saturday: Late morning tea-time, Lazy afternoon, Early night.
    """
    now = get_current_npt_time()
    weekday = now.weekday()  # Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6

    # Define Slots (Hour, Minute) based on Deep Research
    if weekday == 4:    # FRIDAY
        slots = [(14, 15), (19, 15), (22, 30)]
    elif weekday == 5:  # SATURDAY
        slots = [(10, 15), (15, 30), (20, 30)]
    else:               # SUNDAY - THURSDAY
        slots = [(15, 45), (19, 15), (21, 45)]

    iso_strings = []

    for hour, minute in slots:
        # 1. Get the NPT time for today
        npt_dt = get_npt_time_today(hour, minute)
        
        # 2. Validate it's in the future
        safe_npt = validate_schedule_time(npt_dt)
        
        # 3. Convert to UTC ISO for YouTube API
        iso_strings.append(npt_to_utc_iso(safe_npt))

    return iso_strings

# --- EXAMPLE OF HOW TO USE THIS IN YOUR MAIN UPLOAD SCRIPT ---
# daily_times = get_three_daily_schedules()
# video1_time = daily_times[0]
# video2_time = daily_times[1]
# video3_time = daily_times[2]