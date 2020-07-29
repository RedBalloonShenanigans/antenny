try:
    import machine
    import utime

    RTC = machine.RTC()
except ImportError:
    RTC = None
import logging
import struct
import socket
import time

from antenny import AntennyAPI, esp32_antenna_api_factory, mock_antenna_api_factory
from antenny_threading import Thread, Queue, Empty
from multi_client.protocol.constants import HEARTBEAT_PAYLOAD_ACK_TYPE, MOVE_RESPONSE_PAYLOAD_TYPE
from multi_client.protocol.heartbeat import HeartbeatRequest, HeartbeatResponse
from multi_client.protocol.move import MoveRequest, MoveResponse
from multi_client.protocol.packet import MultiAntennyPacket, MultiAntennyPacketHeader

MCAST_GRP = '224.11.11.11'
MCAST_PORT = 31337
IS_ALL_GROUPS = False

LOG = logging.getLogger("antenny.multi_client.follower")

MAX_MESSAGE_SIZE = 1024
_DEFAULT_TIMEOUT = 0.0001

try:
    import ujson as json
except ImportError:
    import json

# Not defined in micropython
INADDR_ANY = 0


def socket_inet_aton(ip_address: str):
    values = ip_address.split('.')
    result = b""
    for value in values:
        result += struct.pack("!B", int(value))
    return result


def create_heartbeat_response_packet(board_id: int):
    return MultiAntennyPacket(
            MultiAntennyPacketHeader(board_id, HEARTBEAT_PAYLOAD_ACK_TYPE, MCAST_PORT),
            HeartbeatResponse(),
    )


def create_move_response_packet(board_id: int, move_ok: bool):
    return MultiAntennyPacket(
            MultiAntennyPacketHeader(board_id, MOVE_RESPONSE_PAYLOAD_TYPE, MCAST_PORT),
            MoveResponse(move_ok),
    )


class FollowerMessage(object):
    def __init__(
            self,
            raw_message: bytes,
    ):
        self.raw_message = raw_message


class UDPFollowerMessage(FollowerMessage):

    def __init__(
            self,
            raw_message: bytes,
            sender_hostname: str,
            sender_port: int,
    ):
        super(UDPFollowerMessage, self).__init__(raw_message)
        self.sender_hostname = sender_hostname
        self.sender_port = sender_port


class FollowerClient(Thread):
    def __init__(
            self,
            inbound_queue: Queue,
            outbound_queue: Queue,
    ):
        super(FollowerClient, self).__init__()
        self.inbound_queue = inbound_queue
        self.outbound_queue = outbound_queue

    def receive(self):
        # type: (...) -> Optional[FollowerMessage]
        try:
            return self.inbound_queue.get(timeout=_DEFAULT_TIMEOUT)
        except Empty:
            return None

    def send(self, message):
        self.outbound_queue.put(message)


class UDPFollowerClient(FollowerClient):

    def __init__(
            self,
            inbound_queue: Queue,
            outbound_queue: Queue,
            listen_port: int
    ):
        super(UDPFollowerClient, self).__init__(inbound_queue, outbound_queue)
        self._multicast_listen_sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
                socket.IPPROTO_UDP
        )
        self._multicast_listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._multicast_listen_sock.bind((MCAST_GRP, listen_port))
        mreq = struct.pack("4sl", socket_inet_aton(MCAST_GRP), INADDR_ANY)
        self._multicast_listen_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self._multicast_listen_sock.settimeout(_DEFAULT_TIMEOUT)
        self._multicast_send_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
                socket.IPPROTO_UDP
        )

    def run(self):
        while self.running:
            self._recv_from_multicast()
            self._send()

    def _send(self):
        try:
            message, addr = self.outbound_queue.get(timeout=_DEFAULT_TIMEOUT)
        except Empty:
            return
        self._multicast_send_socket.sendto(message, addr)

    def _recv_from_multicast(self):
        try:
            message, (hostname, port) = self._multicast_listen_sock.recvfrom(MAX_MESSAGE_SIZE)
        except OSError:
            return
        self.inbound_queue.put(UDPFollowerMessage(message, hostname, port))


class AntennyFollowerNode(Thread):

    def __init__(
            self,
            board_id: int,
            follower_client: FollowerClient,
            api: AntennyAPI,
    ):
        super(AntennyFollowerNode, self).__init__()
        self.board_id = board_id
        self.follower_client = follower_client
        self.api = api
        self.following_id = None
        self._leaders = set()

    def run(self):
        while self.running:
            message = self.follower_client.receive()
            if message is None:
                continue
            packet = MultiAntennyPacket.deserialize(message.raw_message)
            if isinstance(packet.payload, HeartbeatRequest):
                self._handle_heartbeat(packet, message)
            elif isinstance(packet.payload, MoveRequest):
                self._handle_move(packet, message)
            else:
                raise NotImplementedError(
                        "Unable to handle packet type {}".format(type(packet.payload)))

    def follow(self, board_id: int):
        if board_id not in self._leaders:
            LOG.warning("Waiting for leader with ID {} to come online".format(board_id))
            return False
        LOG.debug("Following board_id={}".format(board_id))
        self.following_id = board_id
        return True

    def unfollow(self):
        self.following_id = None

    def available_leaders(self):
        return self._leaders

    def _handle_heartbeat(
            self,
            packet: MultiAntennyPacket,
            message: FollowerMessage,
    ):
        assert isinstance(message, UDPFollowerMessage)
        assert isinstance(packet.payload, HeartbeatRequest)
        self._leaders.add(packet.header.board_id)
        if packet.header.board_id == self.following_id:
            LOG.debug("Got heartbeat from leader id={}".format(self.following_id))
            self.follower_client.send((
                create_heartbeat_response_packet(self.board_id).serialize(),
                (message.sender_hostname, packet.header.listen_port)
            ))
        else:
            LOG.debug("Ignoring heartbeat from leader id={}".format(packet.header.board_id))

    def _handle_move(
            self,
            packet: MultiAntennyPacket,
            message: FollowerMessage,
    ):
        assert isinstance(packet.payload, MoveRequest)
        if packet.payload.board_id != self.board_id:
            LOG.debug("Received a MoveRequest for another device_id={}".format(
                    packet.payload.board_id
            ))
            return
        now = time.time()
        if packet.payload.move_at_timestamp < now:
            LOG.warning("Received a MoveRequest after the given timestamp, NOT moving!")
            return
        delta = packet.payload.move_at_timestamp - now
        delta += packet.payload.move_at_millis - (RTC.datetime()[-1] / 1000000)
        if delta > 10000:
            LOG.debug("Very large time offset.")
            return
        LOG.debug("Sleeping for time delta of {} seconds".format(delta))
        time.sleep(delta)
        self.api.antenna.set_azimuth(packet.payload.azimuth)
        self.api.antenna.set_elevation(packet.payload.elevation)
        assert isinstance(message, UDPFollowerMessage)
        self.follower_client.send((
            create_move_response_packet(self.board_id, move_ok=True).serialize(),
            (message.sender_hostname, packet.header.listen_port)
        ))


def main(board_id: int):
    api = mock_antenna_api_factory(False, False)
    # api = esp32_antenna_api_factory(True, True)
    udp_client = UDPFollowerClient(Queue(), Queue(), MCAST_PORT)
    follower = AntennyFollowerNode(board_id, udp_client, api)
    try:
        udp_client.start()
        follower.start()
        while not follower.follow(0x42):
            time.sleep(0.25)
    except Exception as e:
        print(e)
        udp_client.stop()
        follower.stop()
        return
    follower.join()
    udp_client.join()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('device_id', type=int)
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    main(args.device_id)
