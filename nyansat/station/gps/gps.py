class GPSStatus(object):
    __slots__ = ['valid', 'latitude', 'longitude', 'altitude', 'speed', 'course', 'timestamp']
    def __init__(self, valid: bool, latitude: float, longitude: float, altitude: float, speed: float, course: float,
                 timestamp: float):
        self.valid = valid
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.speed = speed
        self.course = course
        self.timestamp = timestamp


class GPSController(object):
    def run(self):
        raise NotImplementedError()

    def get_status(self):
        raise NotImplementedError
