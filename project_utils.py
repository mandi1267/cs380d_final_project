import time


def getCurrentTimeMillis():
    """
    Get the current time, in milliseconds.

    :return: current time in milliseconds.
    """
    return time.time() * 1000
