import struct

from multi_client.protocol.constants import MOVE_REQUEST_PAYLOAD_TYPE, MOVE_RESPONSE_PAYLOAD_TYPE
from multi_client.protocol.payload import MultiAntennyPayload


class MoveRequest(MultiAntennyPayload):
    STRUCT_FORMAT = '!hhhid'

    def __init__(
            self,
            board_id: int,
            azimuth: int,
            elevation: int,
            move_at_timestamp: int,
            move_at_millis: float,
    ):
        super(MoveRequest, self).__init__(MOVE_REQUEST_PAYLOAD_TYPE)
        self.board_id = board_id
        self.azimuth = azimuth
        self.elevation = elevation
        self.move_at_timestamp = move_at_timestamp
        self.move_at_millis = move_at_millis

    def __repr__(self):
        return "<MoveRequest device_id={} azimuth={} elevation={} move_at={}:{}>".format(
            self.board_id, self.azimuth, self.elevation, self.move_at_timestamp,
            self.move_at_millis)

    def serialize(self):
        packed = struct.pack(
                self.STRUCT_FORMAT,
                self.board_id,
                self.azimuth,
                self.elevation,
                self.move_at_timestamp,
                self.move_at_millis,
        )
        return packed

    @classmethod
    def deserialize(cls, payload: bytes):
        return cls(*struct.unpack(MoveRequest.STRUCT_FORMAT, payload))


class MoveResponse(MultiAntennyPayload):
    STRUCT_FORMAT = '!b'

    def __init__(
            self,
            move_ok: bool,
    ):
        super(MoveResponse, self).__init__(MOVE_RESPONSE_PAYLOAD_TYPE)
        self.move_ok = move_ok

    def serialize(self):
        return struct.pack(self.STRUCT_FORMAT, self.move_ok)

    @classmethod
    def deserialize(cls, payload: bytes):
        return cls(bool(struct.unpack(MoveResponse.STRUCT_FORMAT, payload)[0]))
