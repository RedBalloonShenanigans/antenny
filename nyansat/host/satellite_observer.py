#!/usr/bin/python3

# Mostly adapted from:
# https://gist.github.com/rbs-tim/c1e8de814a92b5c2464143c917af8735

import asyncio
import time

from datetime import datetime
from fuzzywuzzy import process
from typing import Dict, Tuple, Union
from skyfield.api import load, Topos, EarthSatellite
from skyfield.iokit import parse_tle_file


LatLong = Union[float, str]


class SatelliteObserver(object):
    """
    Represents a satellite relative to a specific ground location. Can be
    created automatically from a TLE data file, satellite keyword, and current
    location information.
    """

    # Degrees
    LOWEST_VISIBLE_ELEVATION = 15

    @classmethod
    def parse_tle(cls, coords: Tuple[LatLong, LatLong], sat_name: str,
                  tle_data: Dict) -> 'SatelliteObserver':
        """
        Parse TLE data into a SatelliteObserver object
        :param coords: latitude and longitude of the observer
        :param sat_name: satellite key to get from the TLE list
        :param tle_data: iterable list of TLE data
        :return: SatelliteObserver object
        """
        place = Topos(*coords)
        _satellites = {sat.name: sat for sat in tle_data}
        closest_sat_name, _ = process.extractOne(sat_name, _satellites.keys())
        return cls(place, _satellites[closest_sat_name])

    def __init__(self, observer_location: Topos, satellite: EarthSatellite):
        """
        :param observer_location: location where observation is taking place
        :param satellite: satellite being observed
        """
        self.observer_location = observer_location
        self.sat = satellite
        self.sat_name = satellite.name
        self.timescale = load.timescale(builtin=True)

    def get_stats(self, at_time: float) -> Tuple[float, float, float]:
        """
        Get the altitude, azimuth, and elevation of the satellite at at_time
        :param at_time: Unix time GMT (timestamp) for statellite stats
        :return: (altitude, azimuth, distance)
        """
        gmt = datetime.utcfromtimestamp(at_time)
        timestamp = self.timescale.utc(gmt.year, gmt.month, gmt.day, gmt.hour,
                                       gmt.minute,
                                       gmt.second + gmt.microsecond / 1000000.0)
        difference = self.sat - self.observer_location
        current_difference = difference.at(timestamp)
        altitude, azimuth, distance = current_difference.altaz()
        return altitude.degrees, azimuth.degrees, distance.km

    def get_current_stats(self) -> Tuple[float, float, float]:
        """
        Get the altitude, azimuth, and elevation of the satellite at the
        current time
        :return: (altitude, azimuth, distance)
        """
        return self.get_stats(time.time())

    def get_visible(self) -> bool:
        """
        Return whether or not the satellite is visible at the given time
        :param at_time: the time at which to check satellite visibility
        :return: whether or not the satellite is visible
        """
        elevation, _, _ = self.get_current_stats()
        return elevation > SatelliteObserver.LOWEST_VISIBLE_ELEVATION

