from datetime import datetime


def parse_time(value):
    if not value or value == "None":
        return None

    try:
        return datetime.strptime(value, "%H:%M:%S")
    except Exception:
        return None


def hours_between(start, end):
    start_time = parse_time(start)
    end_time = parse_time(end)

    if not start_time or not end_time:
        return None

    diff = (end_time - start_time).total_seconds() / 3600

    if diff < 0:
        diff += 24

    return round(diff, 2)


def transfer_wait_hours(arrival, departure):
    return hours_between(arrival, departure)


def is_valid_transfer(arrival, departure, min_wait_minutes=30, max_wait_hours=8):
    wait = transfer_wait_hours(arrival, departure)

    if wait is None:
        return False

    min_wait_hours = min_wait_minutes / 60

    return min_wait_hours <= wait <= max_wait_hours