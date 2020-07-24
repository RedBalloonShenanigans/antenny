from multi_client.protocol.constants import HEARTBEAT_PAYLOAD_ACK_TYPE, HEARTBEAT_PAYLOAD_TYPE
from multi_client.protocol.payload import MultiAntennyPayload


class HeartbeatRequest(MultiAntennyPayload):

    def __init__(self):
        super(HeartbeatRequest, self).__init__(HEARTBEAT_PAYLOAD_TYPE)

    def serialize(self):
        return b'heartbeat'

    @classmethod
    def deserialize(cls, payload: bytes):
        return cls()


class HeartbeatResponse(MultiAntennyPayload):

    def __init__(self):
        super(HeartbeatResponse, self).__init__(HEARTBEAT_PAYLOAD_ACK_TYPE)

    def serialize(self):
        return b'heartbeat:ack'

    @classmethod
    def deserialize(cls, payload: bytes):
        return cls()
