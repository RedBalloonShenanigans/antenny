import logging
import socket
import time

try:
    import ujson as json
except ImportError:
    import json

from antenny_threading import Empty, Thread, Queue

_DEFAULT_TIMEOUT = 0.01

LOG = logging.getLogger('telemetry.mock')


class MockTelemetrySender(Thread):

    def __init__(
            self,
            recipient_hostname: str,
            recipient_port: int,
    ):
        super(MockTelemetrySender, self).__init__()
        self._socket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('', 31337))
        self._recipient_address = (recipient_hostname, recipient_port)
        self._update_queue = Queue()

    def run(self):
        while self.running:
            try:
                data = self._update_queue.get(timeout=_DEFAULT_TIMEOUT)
            except Empty:
                continue
            print("sending telemetry!!")
            self._socket.sendto(json.dumps(data).encode('utf-8'), self._recipient_address)

    def update(self, data: dict):
        self._update_queue.put(data)
