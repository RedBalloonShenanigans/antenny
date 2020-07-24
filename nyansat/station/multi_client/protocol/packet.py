import struct

from multi_client.protocol.constants import (
    HEARTBEAT_PAYLOAD_ACK_TYPE, HEARTBEAT_PAYLOAD_TYPE,
    MOVE_REQUEST_PAYLOAD_TYPE, MOVE_RESPONSE_PAYLOAD_TYPE,
)
from multi_client.protocol.heartbeat import HeartbeatRequest, HeartbeatResponse
from multi_client.protocol.move import MoveRequest, MoveResponse
from multi_client.protocol.payload import MultiAntennyPayload


class MultiAntennyPacketHeader(MultiAntennyPayload):
    STRUCT_FORMAT = '!HHH'
    HEADER_LENGTH = 6

    def __init__(
            self,
            board_id: int,
            payload_type: int,
            listen_port: int,
    ):
        self.board_id = board_id
        self.payload_type = payload_type
        self.listen_port = listen_port

    def serialize(self):
        return struct.pack(self.STRUCT_FORMAT, self.board_id, self.payload_type, self.listen_port)

    @classmethod
    def deserialize(cls, payload: bytes):
        board_id, payload_type, listen_port = struct.unpack(
                MultiAntennyPacketHeader.STRUCT_FORMAT,
                payload[:MultiAntennyPacketHeader.HEADER_LENGTH],
        )
        return (
            cls(board_id, payload_type, listen_port),
            payload[MultiAntennyPacketHeader.HEADER_LENGTH:]
        )


class MultiAntennyPacket(object):

    def __init__(
            self,
            header: MultiAntennyPacketHeader,
            payload: MultiAntennyPayload,
    ):
        self.header = header
        self.payload = payload

    def serialize(self):
        return self.header.serialize() + self.payload.serialize()

    @classmethod
    def deserialize(cls, raw_payload: bytes):
        header, payload = MultiAntennyPacketHeader.deserialize(raw_payload)
        if header.payload_type == HEARTBEAT_PAYLOAD_TYPE:
            payload = HeartbeatRequest.deserialize(payload)
        elif header.payload_type == HEARTBEAT_PAYLOAD_ACK_TYPE:
            payload = HeartbeatResponse.deserialize(payload)
        elif header.payload_type == MOVE_REQUEST_PAYLOAD_TYPE:
            payload = MoveRequest.deserialize(payload)
        elif header.payload_type == MOVE_RESPONSE_PAYLOAD_TYPE:
            payload = MoveResponse.deserialize(payload)
        else:
            raise ValueError("Unknown payload type: {}".format(header.payload_type))
        return cls(header, payload)
