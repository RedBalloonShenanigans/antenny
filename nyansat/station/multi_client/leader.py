import logging
import random
import socket
import time

from antenny_threading import Thread, Queue, Empty
from multi_client.common import common_time
from multi_client.protocol.constants import HEARTBEAT_PAYLOAD_TYPE, MOVE_REQUEST_PAYLOAD_TYPE
from multi_client.protocol.heartbeat import HeartbeatRequest, HeartbeatResponse
from multi_client.protocol.move import MoveRequest, MoveResponse
from multi_client.protocol.packet import MultiAntennyPacket, MultiAntennyPacketHeader

MULTICAST_ADDR = "224.11.11.11"
_DEFAULT_TIMEOUT = 0.0001
LOG = logging.getLogger("antenny.multi_client.leader")


def create_heartbeat_request_packet(board_id: int, listen_port: int):
    return MultiAntennyPacket(
            MultiAntennyPacketHeader(board_id, HEARTBEAT_PAYLOAD_TYPE, listen_port),
            HeartbeatRequest(),
    )


def create_move_request_packet(
        from_board_id: int,
        to_board_id: int,
        azimuth: int,
        elevation: int,
        move_at_timestamp: int,
        move_at_millis: float,
        listen_port: int,
):
    return MultiAntennyPacket(
            MultiAntennyPacketHeader(from_board_id, MOVE_REQUEST_PAYLOAD_TYPE, listen_port),
            MoveRequest(to_board_id, azimuth, elevation, move_at_timestamp, move_at_millis),
    )


class LeaderClient(Thread):

    def __init__(
            self,
            outbound_queue: Queue,
            inbound_queue: Queue,
    ):
        super(LeaderClient, self).__init__()
        self.outbound_queue = outbound_queue
        self.inbound_queue = inbound_queue
        self._payloads_by_packet_type = {}

    def recv(
            self,
            payload_type,  # type: Type[MultiAntennyPayload]
    ):
        """
        Fetch a packet from the queue, of a specific payload type
        """
        try:
            recv = self.inbound_queue.get(timeout=_DEFAULT_TIMEOUT)
        except Empty:
            return None
        while recv is not None:
            curr_payload_type = type(recv.payload)
            if curr_payload_type not in self._payloads_by_packet_type:
                self._payloads_by_packet_type[curr_payload_type] = Queue()
            self._payloads_by_packet_type[curr_payload_type].put(recv)
            try:
                recv = self.inbound_queue.get(timeout=_DEFAULT_TIMEOUT)
            except Empty:
                break
        try:
            return self._payloads_by_packet_type[payload_type].get(timeout=_DEFAULT_TIMEOUT)
        except (Empty, KeyError):
            return None

    def send(self, message):
        self.outbound_queue.put(message)


class UDPLeaderClient(LeaderClient):
    def __init__(
            self,
            outbound_queue: Queue,
            inbound_queue: Queue,
            broadcast_port: int,
            listen_port: int,
    ):
        super(UDPLeaderClient, self).__init__(outbound_queue, inbound_queue)
        self._port = broadcast_port
        self._mcast_send_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
                socket.IPPROTO_UDP
        )
        self._mcast_send_socket.settimeout(0.01)
        self._mcast_send_socket.bind(('', listen_port))

    def _send(self):
        """
        Send any queued outbound messages
        """
        try:
            message = self.outbound_queue.get()
        except Empty:
            return
        self._mcast_send_socket.sendto(message, (MULTICAST_ADDR, self._port))

    def run(self):
        while self.running:
            self._send()
            self._recv()

    def _recv(self):
        try:
            raw_message, _ = self._mcast_send_socket.recvfrom(1024)
        except OSError:
            return
        self.inbound_queue.put(MultiAntennyPacket.deserialize(raw_message))


class OnlineDevice(object):

    def __init__(
            self,
            device_id: int,
            last_online: float,
            round_trip_times,  # type: List[float]
    ):
        self.device_id = device_id
        self.last_online = last_online
        self.round_trip_times = round_trip_times

    def __repr__(self):
        return "<Device device_id={} online={} avg RTT={}>".format(
                self.device_id,
                self.is_online(),
                self.average_rtt()
        )

    def is_online(self, offline_time=10):
        return common_time() - self.last_online < offline_time

    def add_rtt(self, new_rtt: float):
        self.last_online = common_time()
        self.round_trip_times.append(new_rtt)

    def average_rtt(self):
        return sum(self.round_trip_times) / len(self.round_trip_times)


class HeartbeatThread(Thread):

    def __init__(
            self,
            board_id: int,
            listen_port: int,
            client: LeaderClient,
    ):
        super(HeartbeatThread, self).__init__()
        self.board_id = board_id
        self.client = client
        self.listen_port = listen_port
        self._online_devices = {}

    def get_device_info(self, device_id):
        # type: (int) -> Optional[OnlineDevice]
        try:
            return self._online_devices[device_id]
        except KeyError:
            return None

    def hearbeat(self):
        heart_beat = common_time()
        serialized = create_heartbeat_request_packet(self.board_id, self.listen_port).serialize()
        self.client.send(serialized)
        delay = 0
        while delay < 0.25:
            time.sleep(_DEFAULT_TIMEOUT)
            delay += _DEFAULT_TIMEOUT
            recv = self.client.recv(HeartbeatResponse)
            while recv is not None:
                device_id = recv.header.board_id
                if device_id not in self._online_devices:
                    self._online_devices[device_id] = OnlineDevice(
                            device_id,
                            heart_beat + delay,
                            [delay]
                    )
                else:
                    self._online_devices[device_id].add_rtt(delay)
                recv = self.client.recv(HeartbeatResponse)
        for device in self._online_devices.values():
            print(device)

    def run(self):
        while self.running:
            self.hearbeat()
            time.sleep(.5)


class AntennyLeader(object):

    def __init__(
            self,
            board_id: int,
            listen_port: int,
            leader_client: LeaderClient,
            heartbeat: HeartbeatThread,
    ):
        self.board_id = board_id
        self.listen_port = listen_port
        self.client = leader_client
        self.heartbeat = heartbeat

    def start(self):
        self.heartbeat.start()

    def stop(self):
        self.heartbeat.stop()

    def wait_for_devices(
            self,
            device_ids,
            max_delay=10,
    ):
        # type: (List[int]) -> None
        LOG.info("Waiting for devices {}".format(device_ids))
        waited_for = 0
        while True:
            if all([self.heartbeat.get_device_info(device_id)
                    is not None for device_id in device_ids]):
                break
            waited_for += _DEFAULT_TIMEOUT
            time.sleep(_DEFAULT_TIMEOUT)
            if waited_for >= max_delay:
                raise RuntimeError("Not all devices came online within the max delay time.")

    def move(
            self,
            device_id: int,
            azimuth: int,
            elevation: int,
            move_at_timestamp: float,
    ):
        device_info = self.heartbeat.get_device_info(device_id)  # type: Optional[OnlineDevice]
        if device_info is None:
            LOG.warning(
                    "Not sending move command to an unknown device with ID '{}'".format(device_id))
            return
        if not device_info.is_online():
            LOG.warning("Not sending move command to an offline device")
            return
        rtt_delta = device_info.average_rtt()
        move_at = move_at_timestamp - (rtt_delta / 2)  # 1/2 full RTT delay
        move_packet = create_move_request_packet(
                self.board_id,
                device_id,
                azimuth,
                elevation,
                int(move_at),
                move_at - int(move_at),
                self.listen_port,
        )
        self.client.send(move_packet.serialize())


def y2k_timestamp():
    return time.time() - 946684800.0


def programmed_move_demo(device_ids, moves):
    for el, az, delay in moves:
        for device_id in device_ids:
            leader.move(device_id, az, el, y2k_timestamp() + 1)
        time.sleep(delay)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    board_id = 0x42
    listen_port = 44444
    udp_client = UDPLeaderClient(Queue(), Queue(), 31337, listen_port)
    udp_client.start()
    heartbeat = HeartbeatThread(board_id, listen_port, udp_client)
    leader = AntennyLeader(board_id, listen_port, udp_client, heartbeat)
    try:
        leader.start()
        leader.wait_for_devices([1, 2])
        # leader.wait_for_devices([1])
        for _ in range(1000):
            moves = []
            for _ in range(10):
                moves.append((random.randint(5, 175), random.randint(5, 175), 2))
            programmed_move_demo(
                    [1, 2],
                    moves,
            )
    except:
        leader.stop()
        udp_client.stop()
