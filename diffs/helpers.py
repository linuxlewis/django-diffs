import time

from django.utils import timezone


def precise_timestamp(dt=None):
    """Returns a float representing a utc timestamp with milliseconds."""
    now = dt or timezone.now()
    return time.mktime(now.utctimetuple()) * 1000 + now.microsecond / 1000