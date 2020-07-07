import _thread
import config as cfg
import socket
import ujson

class TelemetrySenderUDP:
    """Send key-value data over UDP to be displayed on client end."""

    def __init__(self):
        """Create a TelemetrySenderUDP object with destination address and port
        obtained from the current user-set config.
        """
        self.socket_lock = _thread.allocate_lock()
        self.cur_telem = {}
        self.cur_telem['euler'] = ()
        self.cur_telem['gps'] = ()
        self.cur_telem['last_time'] = 0
        self.dstaddr = cfg.get("telem_destaddr")
        self.dstport = cfg.get("telem_destport")
        self.mcast_send_socket = None
        self.init_socket()

    def init_socket(self):
        self.mcast_send_socket = socket.socket(socket.AF_INET,
                socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    def set_destination(self, multicast_ipaddr):
        self.dstaddr = multicast_ipaddr
        self.init_socket()

    def update_telem(self, dict_vals: dict):
        """Update the key-value mapping to be sent over UDP."""
        for key, val in dict_vals.items():
            with self.socket_lock:
                self.cur_telem[key] = val

    def send_telem_tick(self):
        """Send the key-value mapping to the destination address and port in
        JSON string format.
        """
        with self.socket_lock:
            tick_str = ujson.dumps(self.cur_telem)
            self.mcast_send_socket.sendto(tick_str, (self.dstaddr, self.dstport))