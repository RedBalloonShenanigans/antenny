import logging
import socket
import time
import traceback

from nyansat.station.mesh_network.packet import (
    AntennyControlEnvelope, AntennyControlPacket, AntennyControlPacketPayload,
    AntennyMoveRequestPayload, AntennyMoveResponsePayload, AntennyPingRequest,
    AntennyPingResponse, AntennyStatusRequestPayload, AntennyStatusResponsePayload, MAX_PACKET_SIZE,
)

LOG = logging.getLogger('antenny.mesh.follower')


class AntennyMeshFollower(object):

    def __init__(
            self,
            device_id: int,
            channel_id: int,
            listen_port: int,
    ):
        self.device_id = device_id
        self.channel_id = channel_id
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('', listen_port))
        self._running = False

    def run(self):
        while self._running:
            msg, addr = self._socket.recvfrom(MAX_PACKET_SIZE)
            control_packet = AntennyControlPacket.deserialize(msg)
            if control_packet.header.channel != self.channel_id:
                LOG.debug("Received a packet for channel '{}', discarding".format(
                        hex(control_packet.header.channel)
                ))
                continue
            # Route the packet to the handler based on packet type
            if isinstance(control_packet.payload, AntennyPingRequest):
                self._handle_ping(control_packet, addr)
            elif isinstance(control_packet.payload, AntennyMoveRequestPayload):
                self._handle_move(control_packet, addr)
            elif isinstance(control_packet.payload, AntennyStatusRequestPayload):
                self._handle_status_request(control_packet, addr)
            else:
                raise NotImplementedError("Doesn't handle {} payloads".format(
                        type(control_packet.payload)
                ))

    def start(self):
        self._running = True
        self.run()

    def join(self):
        self._running = False

    def _send_response(
            self,
            control_packet: AntennyControlPacketPayload,
            command_type: int,
            sender_addr,  # type: Tuple[str, int]
    ):
        response = AntennyControlPacket(
                AntennyControlEnvelope(
                        self.device_id,
                        self.channel_id,
                        command_type,
                        None
                ),
                control_packet
        )
        self._socket.sendto(response.serialize(), sender_addr)

    def _handle_ping(
            self,
            packet: AntennyControlPacket,
            sender_addr,  # type: Tuple[str, int]
    ):
        delta = time.time() - packet.payload.sent_at
        host, port = sender_addr
        LOG.info("Got ping from {}:{}; Time of Flight: {}".format(host, port, delta))
        self._send_response(
                AntennyPingResponse(time.time()),
                AntennyPingResponse.COMMAND_TYPE,
                sender_addr,
        )

    def _handle_move(
            self,
            packet: AntennyControlPacket,
            sender_addr,  # type: Tuple[str, int]
    ):

        if packet.payload.device_id != self.device_id:
            LOG.debug("Ignoring move command for device id '{}'".format(
                    hex(packet.payload.device_id))
            )
            return
        LOG.info("MOVE!")
        self._send_response(
                AntennyMoveResponsePayload(self.device_id, True),
                AntennyMoveResponsePayload.COMMAND_TYPE,
                sender_addr,
        )

    def _handle_status_request(
            self,
            packet: AntennyControlPacket,
            sender_addr,  # type: Tuple[str, int]
    ):
        if packet.payload.device_id != self.device_id:
            LOG.debug("Ignoring status request for device id '{}'".format(
                    hex(packet.payload.device_id))
            )
            return
        LOG.info("Status")
        fake_az, fake_el, fake_lat, fake_lon = 0, 0, 0, 0
        self._send_response(
                AntennyStatusResponsePayload(
                        self.device_id,
                        fake_az,
                        fake_el,
                        fake_lat,
                        fake_lon,
                ),
                AntennyStatusResponsePayload.COMMAND_TYPE,
                sender_addr,
        )


if __name__ == '__main__':
    logging.basicConfig(
            format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
            level=logging.DEBUG,
            datefmt='%Y-%m-%d %H:%M:%S'
    )
    follower = AntennyMeshFollower(0x42, 0xf00dbabe, 37020)
    try:
        follower.start()
    except Exception as e:
        print(e)
        traceback.print_exc()
        follower.join()
    follower.join()
