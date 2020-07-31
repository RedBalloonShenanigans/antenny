import time

from gps.gps import GPSController, GPSStatus


class MockGPSController(GPSController):

    def run(self):
        pass

    def get_status(self):
        return GPSStatus(
                valid=True,
                latitude=40.704342,
                longitude=-74.018468,
                altitude=10,
                speed=0.,
                course=0.,
                timestamp=time.time(),
        )
