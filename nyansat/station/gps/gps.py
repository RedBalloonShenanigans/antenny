from abc import ABC, abstractmethod
from typing import Optional

from attr import dataclass


@dataclass
class GPSStatus:
    valid: bool
    latitude: float
    longitude: float
    altitude: float
    speed: float
    course: float
    timestamp: float


class GPSController(ABC):
    @abstractmethod
    def run(self):
        raise NotImplementedError()

    @abstractmethod
    def get_status(self) -> Optional[GPSStatus]:
        raise NotImplementedError
