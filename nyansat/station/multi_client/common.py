import time

try:
    import machine

    RTC = machine.RTC()
except ImportError:
    machine = None
    RTC = None


def common_time():
    """
    Common python/micropython time wrapper.
    """
    if machine is None:
        return time.time()
    return time.time() + RTC.datetime()[-1] / 1000000
