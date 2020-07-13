import struct
import time
from datetime import datetime

MAX_PACKET_SIZE = 1024

"""
1 payload / packet

## Envelope:
4 bytes: Header magic
2 bytes: board id
8 bytes: shared channel
1 byte: command type
{payload, variable}
4 bytes: Tail magic

## Move Request (0x01)
4 bytes: time to move (UNIX timestamp)
4 bytes: move duration (seconds)
2 bytes: azimuth
2 bytes: elevation

## Move Response (0x02)
1 byte: move ok (bool)

## Status Request (0x03)
- No body -

## Status Response (0x04)
2 bytes: azimuth
2 bytes: elevation
4 bytes: lat (optional)
4 bytes: lon (optional)


## Ping Request (0x05)
4 bytes: ping initiated at

## Ping Response (0x06)
4 bytes: ping recieved at
"""


class AntennyControlPacketPayload(object):

    def serialize(self) -> bytes:
        raise NotImplementedError

    @staticmethod
    def deserialize(serialized_payload: bytes):
        raise NotImplementedError


class AntennyControlEnvelope(object):
    """
    Antenny control packet outer envelope.
    """
    ENVELOPE_HEADER_MAGIC = b'0547'  # sat
    ENVELOPE_TAIL_MAGIC = b'E547'  # e(nd) sat
    STRUCT_FORMAT = '!hQB'

    __slots__ = ('device_id', 'channel', 'command_type', 'payload',)

    def __init__(
            self,
            device_id: int,
            channel: int,
            command_type: int,
            payload,  # type: Optional[bytes]
    ):
        self.device_id = device_id
        self.channel = channel
        self.command_type = command_type
        self.payload = payload

    def __str__(self):
        return "<AntennyControlEnvelope ID: {} Channel: {}; Command type: {}>".format(
                hex(self.device_id),
                hex(self.channel),
                hex(self.command_type),
        )

    def __repr__(self):
        return str(self)

    def serialize(
            self,
            payload: bytes,
    ) -> bytes:
        envelope = struct.pack(self.STRUCT_FORMAT, self.device_id, self.channel, self.command_type)
        return self.ENVELOPE_HEADER_MAGIC + envelope + payload + self.ENVELOPE_TAIL_MAGIC

    @staticmethod
    def deserialize(serialized_packet: bytes) -> 'AntennyControlEnvelope':
        if serialized_packet[:4] != AntennyControlEnvelope.ENVELOPE_HEADER_MAGIC:
            raise ValueError("Invalid header magic")
        if serialized_packet[-4:] != AntennyControlEnvelope.ENVELOPE_TAIL_MAGIC:
            raise ValueError("Invalid tail magic")
        board_id, shared_secret, command_type = struct.unpack(
                AntennyControlEnvelope.STRUCT_FORMAT,
                serialized_packet[4:15]
        )
        return AntennyControlEnvelope(
                board_id,
                shared_secret,
                command_type,
                serialized_packet[15:-4],
        )


class AntennyMoveRequestPayload(AntennyControlPacketPayload):
    """
    Payload to command a follower to move (0x01)
    """
    STRUCT_FORMAT = "!hdIHH"
    COMMAND_TYPE = 0x01

    __slots__ = ('device_id', 'do_move_at', 'move_duration', 'azimuth', 'elevation',)

    def __init__(
            self,
            device_id: int,
            do_move_at: float,
            move_duration: int,
            azimuth: int,
            elevation: int,
    ):
        self.device_id = device_id
        self.do_move_at = do_move_at
        self.move_duration = move_duration
        self.azimuth = azimuth
        self.elevation = elevation

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "<AntennyMoveRequestPayload {}: {} second(s) azimuth: {} elevation: {}>".format(
                datetime.fromtimestamp(self.do_move_at),
                self.move_duration,
                self.azimuth,
                self.elevation,
        )

    def serialize(self):
        return struct.pack(
                self.STRUCT_FORMAT,
                self.device_id,
                self.do_move_at,
                self.move_duration,
                self.azimuth,
                self.elevation,
        )

    @staticmethod
    def deserialize(serialized_payload: bytes) -> 'AntennyMoveRequestPayload':
        device_id, time_to_move, move_duration, azimuth_target, elevation_target = struct.unpack(
                AntennyMoveRequestPayload.STRUCT_FORMAT,
                serialized_payload
        )
        return AntennyMoveRequestPayload(
                device_id,
                time_to_move,
                move_duration,
                azimuth_target,
                elevation_target
        )


class AntennyMoveResponsePayload(AntennyControlPacketPayload):
    COMMAND_TYPE = 0x02
    __slots__ = ('device_id', 'move_ok',)
    STRUCT_FORMAT = '!h?'

    def __init__(
            self,
            device_id: int,
            move_ok: bool
    ):
        self.device_id = device_id
        self.move_ok = move_ok

    def __str__(self):
        return "<AntennyMoveResponsePayload device id: {} ok?: {}>".format(
                self.device_id, self.move_ok
        )

    def __repr__(self):
        return str(self)

    def serialize(self) -> bytes:
        return struct.pack(self.STRUCT_FORMAT, self.device_id, self.move_ok)

    @staticmethod
    def deserialize(serialized_packet: bytes) -> 'AntennyMoveResponsePayload':
        device_id, move_ok = struct.unpack(
                AntennyMoveResponsePayload.STRUCT_FORMAT,
                serialized_packet[:6]
        )
        return AntennyMoveResponsePayload(device_id, move_ok)


class AntennyStatusRequestPayload(AntennyControlPacketPayload):
    """
    Payload to request a status update from each follower (from the leader)
    """
    __slots__ = ('device_id',)
    STRUCT_FORMAT = '!h'
    COMMAND_TYPE = 0x03

    def __init__(
            self,
            device_id: int,
    ):
        self.device_id = device_id

    def __str__(self):
        return "<AntennyStatusRequestPayload>"

    def __repr__(self):
        return str(self)

    def serialize(self) -> bytes:
        return struct.pack(self.STRUCT_FORMAT, self.device_id)

    @staticmethod
    def deserialize(serialized_payload: bytes) -> 'AntennyStatusRequestPayload':
        device_id = struct.unpack(
                AntennyStatusRequestPayload.STRUCT_FORMAT,
                serialized_payload[:2]
        )[0]
        return AntennyStatusRequestPayload(device_id)


class AntennyStatusResponsePayload(AntennyControlPacketPayload):
    """
    Payload to respond with current antenny status.
    """
    COMMAND_TYPE = 0x04
    STRUCT_FORMAT = "!hHHII"

    def __init__(
            self,
            device_id: int,
            azimuth: int,
            elevation: int,
            lat: int,
            lon: int,
    ):
        self.device_id = device_id
        self.azimuth = azimuth
        self.elevation = elevation
        self.lat = lat
        self.lon = lon

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "<AntennyStatusResponsePayload: {} ({}, {}) @ {}, {}>".format(
                hex(self.device_id),
                self.lat,
                self.lon,
                self.azimuth,
                self.elevation
        )

    def serialize(self) -> bytes:
        return struct.pack(
                self.STRUCT_FORMAT,
                self.device_id,
                self.azimuth,
                self.elevation,
                self.lat,
                self.lon,
        )

    @staticmethod
    def deserialize(serialized_payload: bytes) -> 'AntennyStatusResponsePayload':
        device_id, az, el, lat, lon = struct.unpack(
                AntennyStatusResponsePayload.STRUCT_FORMAT,
                serialized_payload
        )
        return AntennyStatusResponsePayload(device_id, az, el, lat, lon)


class AntennyPingRequest(AntennyControlPacketPayload):
    COMMAND_TYPE = 0x05
    STRUCT_FORMAT = "!d"

    def __init__(
            self,
            sent_at: float,
    ):
        self.sent_at = sent_at

    def __str__(self):
        return "<AntennyPingRequest @ {}>".format(datetime.fromtimestamp(self.sent_at))

    def __repr__(self):
        return str(self)

    def serialize(self) -> bytes:
        return struct.pack(self.STRUCT_FORMAT, self.sent_at)

    @staticmethod
    def deserialize(serialized_payload: bytes):
        sent_at = struct.unpack(AntennyPingRequest.STRUCT_FORMAT, serialized_payload)[0]
        return AntennyPingRequest(sent_at)


class AntennyPingResponse(AntennyControlPacketPayload):
    COMMAND_TYPE = 0x06
    STRUCT_FORMAT = "!d"

    def __init__(
            self,
            received_at: float,
    ):
        self.received_at = received_at

    def __str__(self):
        return "<AntennyPingResponse @ {}>".format(datetime.fromtimestamp(self.received_at))

    def __repr__(self):
        return str(self)

    def serialize(self) -> bytes:
        return struct.pack(self.STRUCT_FORMAT, self.received_at)

    @staticmethod
    def deserialize(serialized_payload: bytes):
        received_at = struct.unpack(AntennyPingResponse.STRUCT_FORMAT, serialized_payload)[0]
        return AntennyPingResponse(received_at)


class AntennyControlPacket(object):

    def __init__(
            self,
            header: AntennyControlEnvelope,
            payload: AntennyControlPacketPayload,
    ):
        self.header = header
        self.payload = payload

    def __str__(self):
        return "<AntennyControlPacket {} {}>".format(str(self.header), str(self.payload))

    def __repr__(self):
        return str(self)

    def serialize(self) -> bytes:
        serialized_packet = self.header.serialize(self.payload.serialize())
        if len(serialized_packet) > MAX_PACKET_SIZE:
            raise ValueError("Packet size exceeds MAX_PACKET_SIZE!")
        return serialized_packet

    @staticmethod
    def deserialize(serialized_packet: bytes) -> 'AntennyControlPacket':
        envelope = AntennyControlEnvelope.deserialize(serialized_packet)
        if envelope.command_type == AntennyMoveRequestPayload.COMMAND_TYPE:  # 0x01
            payload = AntennyMoveRequestPayload.deserialize(envelope.payload)
        elif envelope.command_type == AntennyMoveResponsePayload.COMMAND_TYPE:  # 0x02
            payload = AntennyMoveResponsePayload.deserialize(envelope.payload)
        elif envelope.command_type == AntennyStatusRequestPayload.COMMAND_TYPE:  # 0x03
            payload = AntennyStatusRequestPayload.deserialize(envelope.payload)
        elif envelope.command_type == AntennyStatusResponsePayload.COMMAND_TYPE:  # 0x04
            payload = AntennyStatusResponsePayload.deserialize(envelope.payload)
        elif envelope.command_type == AntennyPingRequest.COMMAND_TYPE:  # 0x05
            payload = AntennyPingRequest.deserialize(envelope.payload)
        elif envelope.command_type == AntennyPingResponse.COMMAND_TYPE:  # 0x06
            payload = AntennyPingResponse.deserialize(envelope.payload)
        else:
            raise ValueError("Unknown command type: {}".format(envelope.command_type))
        return AntennyControlPacket(envelope, payload)


def move_request_serialization_test():
    """
    Test serialization & deserialization for move at packets
    :return:
    """
    test_id = 0x42
    test_device_id = 0x1337
    test_channel = 0xf00dbabe
    command_type = AntennyMoveRequestPayload.COMMAND_TYPE
    test_move_at = int(time.time()) + 1
    test_duration = 1
    test_az_el = 90
    move_request = AntennyMoveRequestPayload(
            test_device_id,
            test_move_at,
            test_duration,
            test_az_el,
            test_az_el,
    )
    env = AntennyControlEnvelope(test_id, test_channel, command_type, None)
    packet = AntennyControlPacket(env, move_request)
    serialized_packet = packet.serialize()
    deserialized = AntennyControlPacket.deserialize(serialized_packet)
    print(deserialized)
    # test header deserialization
    assert deserialized.header.device_id == test_id
    assert deserialized.header.channel == test_channel
    assert deserialized.header.command_type == command_type
    # test payload deserialization
    assert deserialized.payload.device_id == test_device_id
    assert deserialized.payload.do_move_at == test_move_at
    assert deserialized.payload.move_duration == test_duration
    assert deserialized.payload.azimuth == test_az_el
    assert deserialized.payload.elevation == test_az_el


def move_response_serialization_test():
    test_id = 0x42
    test_device_id = 0x1337
    test_channel = 0xf00dbabe
    command_type = AntennyMoveResponsePayload.COMMAND_TYPE
    test_move_ok = True
    move_request = AntennyMoveResponsePayload(test_device_id, test_move_ok)
    env = AntennyControlEnvelope(test_id, test_channel, command_type, None)
    packet = AntennyControlPacket(env, move_request)
    serialized_packet = packet.serialize()
    deserialized = AntennyControlPacket.deserialize(serialized_packet)
    print(deserialized)
    assert deserialized.payload.move_ok == test_move_ok


def status_request_serialization_test():
    test_id = 0x42
    test_device_id = 0x1337
    test_channel = 0xf00dbabe
    command_type = AntennyStatusRequestPayload.COMMAND_TYPE
    move_request = AntennyStatusRequestPayload(test_device_id)
    env = AntennyControlEnvelope(test_id, test_channel, command_type, None)
    packet = AntennyControlPacket(env, move_request)
    serialized_packet = packet.serialize()
    deserialized = AntennyControlPacket.deserialize(serialized_packet)
    print(deserialized)
    assert isinstance(deserialized.payload, AntennyStatusRequestPayload)


def status_response_serialization_test():
    test_id = 0x42
    test_channel = 0xf00dbabe
    command_type = AntennyStatusResponsePayload.COMMAND_TYPE
    test_lat_lon, test_el_az = 45, 90
    move_request = AntennyStatusResponsePayload(test_el_az, test_el_az, test_lat_lon, test_lat_lon)
    env = AntennyControlEnvelope(test_id, test_channel, command_type, None)
    packet = AntennyControlPacket(env, move_request)
    serialized_packet = packet.serialize()
    deserialized = AntennyControlPacket.deserialize(serialized_packet)
    print(deserialized)
    assert isinstance(deserialized.payload, AntennyStatusResponsePayload)
    assert deserialized.payload.azimuth == test_el_az
    assert deserialized.payload.elevation == test_el_az
    assert deserialized.payload.lat == test_lat_lon
    assert deserialized.payload.lon == test_lat_lon


def ping_request_response_serialization_test():
    # Ping
    test_id = 0x42
    test_channel = 0xf00dbabe
    command_type = AntennyPingRequest.COMMAND_TYPE
    sent_at = time.time()
    move_request = AntennyPingRequest(sent_at)
    env = AntennyControlEnvelope(test_id, test_channel, command_type, None)
    packet = AntennyControlPacket(env, move_request)
    serialized_packet = packet.serialize()
    deserialized = AntennyControlPacket.deserialize(serialized_packet)
    print(deserialized)
    assert deserialized.payload.sent_at == sent_at
    # pong
    test_id = 0x42
    test_channel = 0xf00dbabe
    command_type = AntennyPingResponse.COMMAND_TYPE
    sent_at = time.time()
    move_request = AntennyPingResponse(sent_at)
    env = AntennyControlEnvelope(test_id, test_channel, command_type, None)
    packet = AntennyControlPacket(env, move_request)
    serialized_packet = packet.serialize()
    deserialized = AntennyControlPacket.deserialize(serialized_packet)
    print(deserialized)
    assert deserialized.payload.received_at == sent_at


if __name__ == '__main__':
    move_request_serialization_test()
    move_response_serialization_test()
    status_request_serialization_test()
    status_response_serialization_test()
    ping_request_response_serialization_test()
