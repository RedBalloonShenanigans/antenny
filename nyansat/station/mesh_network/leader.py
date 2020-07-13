import logging
import socket
import threading
import time
import traceback
from queue import Queue

from nyansat.station.mesh_network.packet import (
    AntennyControlEnvelope, AntennyControlPacket,
    AntennyControlPacketPayload, AntennyMoveRequestPayload, AntennyMoveResponsePayload,
    AntennyPingRequest, AntennyPingResponse,
    AntennyStatusRequestPayload, AntennyStatusResponsePayload, MAX_PACKET_SIZE,
)

_BROADCAST_ADDR = '<broadcast>'
_TIMEOUT_DELAY = 0.2

LOG = logging.getLogger('antenny.mesh.leader')


class AntennyMeshLeader(object):

    def __init__(
            self,
            device_id: int,
            channel_id: int,
            broadcast_port: int,
            listen_port: int,
    ):
        self.device_id = device_id
        self.channel_id = channel_id
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        self._socket.settimeout(_TIMEOUT_DELAY)
        self._socket.bind(("", listen_port))
        self._broadcast_port = broadcast_port
        self._listen_port = listen_port
        self._send_thread = None
        self._recv_thread = None
        self._outbound_queue = Queue()
        self._inbound_queue_by_packet_type = {
            AntennyPingResponse: Queue(),
            AntennyMoveResponsePayload: Queue(),
            AntennyStatusResponsePayload: Queue(),
        }  # type: Dict[Type[AntennyControlPacketPayload], Queue[AntennyControlPacket]]
        self._last_ping_timestamp = None
        self._last_ping_response_timestamp_by_device_id = {}

    def _send_loop(self):
        while self._running:
            try:
                message = self._outbound_queue.get(timeout=_TIMEOUT_DELAY)
            except:
                continue
            LOG.debug("Sending message")
            self._socket.sendto(message, (_BROADCAST_ADDR, self._broadcast_port))

    def _recv_loop(self):
        while self._running:
            try:
                recv = self._socket.recv(MAX_PACKET_SIZE)
            except:
                continue
            packet = AntennyControlPacket.deserialize(recv)
            if packet.header.channel != self.channel_id:
                LOG.debug("Received a packet for channel '{}', discarding".format(
                        packet.header.channel
                ))
            if packet.payload.__class__ not in self._inbound_queue_by_packet_type:
                raise ValueError("Leader not expecting '{}' packets".format(
                        packet.payload.__class__
                ))
            self._inbound_queue_by_packet_type[packet.payload.__class__].put(packet)

    def start(self):
        self._running = True
        self._send_thread = threading.Thread(target=self._send_loop, args=())
        self._recv_thread = threading.Thread(target=self._recv_loop, args=())
        self._send_thread.start()
        self._recv_thread.start()

    def join(self):
        self._running = False

    def _send_command(
            self,
            control_packet: AntennyControlPacketPayload,
            command_type: int,
    ) -> None:
        packet = AntennyControlPacket(
                AntennyControlEnvelope(
                        self.device_id,
                        self.channel_id,
                        command_type,
                        None
                ),
                control_packet
        )
        self._outbound_queue.put(packet.serialize())

    def ping(
            self,
            max_rtt=.25,
    ):
        LOG.info("Sending a ping to all devices")
        self._send_command(
                AntennyPingRequest(int(time.time())),
                AntennyPingRequest.COMMAND_TYPE,
        )
        curr_time = t1 = time.time()
        ping_response_queue = self._inbound_queue_by_packet_type[AntennyPingResponse]
        while (curr_time - t1) < max_rtt:
            curr_time = time.time()
            try:
                response = ping_response_queue.get(timeout=0.01)
            except:
                continue
            assert isinstance(response, AntennyControlPacket)
            assert isinstance(response.payload, AntennyPingResponse)
            self._last_ping_response_timestamp_by_device_id[response.header.device_id] = curr_time
        LOG.debug("Finished ping")

    def _get_response_from_device(
            self,
            response_type,  # type: Type[AntennyControlPacketPayload]
            device_id: int,
    ):
        queue = self._inbound_queue_by_packet_type[response_type]
        while self._running:
            try:
                message = queue.get(timeout=_TIMEOUT_DELAY)
            except:
                continue
            # Put the messages for other devices back
            if message.payload.device_id != device_id:
                queue.put(message)
                continue
            return message

    def move(
            self,
            device_id: int,
            do_move_at: float,
            move_duration: int,
            azimuth: int,
            elevation: int,
    ):
        LOG.info("Sending move command to device id '{}'".format(hex(device_id)))
        self._send_command(
                AntennyMoveRequestPayload(device_id, do_move_at, move_duration, azimuth, elevation),
                AntennyMoveRequestPayload.COMMAND_TYPE,
        )
        move_response = self._get_response_from_device(
                AntennyMoveResponsePayload,
                device_id,
        )
        LOG.info("Move finished!")

    def get_status(
            self,
            device_id: int,
    ):
        LOG.debug("Getting device id {} status".format(hex(device_id)))
        self._send_command(
                AntennyStatusRequestPayload(device_id),
                AntennyStatusRequestPayload.COMMAND_TYPE,
        )
        status_response = self._get_response_from_device(
                AntennyStatusResponsePayload,
                device_id,
        )
        LOG.debug(status_response.payload)


if __name__ == '__main__':
    logging.basicConfig(
            format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
            level=logging.DEBUG,
            datefmt='%Y-%m-%d %H:%M:%S'
    )
    # TODO: have a thread to ping all devices
    # TODO: have a list of devices that have gone offline after no ping after TTL?
    leader = AntennyMeshLeader(0, 0xf00dbabe, 37020, 44444)
    try:
        leader.start()
        leader.move(0x42, time.time() + 10, 1, 90, 90)
        leader.get_status(0x42)
        for _ in range(2):
            leader.ping()
    except Exception as e:
        traceback.print_exc()
        print(e)
        leader.join()
    leader.join()
