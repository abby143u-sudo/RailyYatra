from backend.services.time_utils import hours_between


def calculate_direct_duration(departure, arrival):
    return hours_between(departure, arrival)


def calculate_transfer_duration(source_departure, destination_arrival):
    return hours_between(source_departure, destination_arrival)