import _thread
import config as cfg
import socket
import ujson

class TelemetrySenderUDP:

    def __init__(self):
        self.socket_lock = _thread.allocate_lock()
        self.cur_telem = {}
        self.cur_telem['euler'] = ()
        self.cur_telem['gps'] = ()
        self.cur_telem['last_time'] = 0
        self.dstaddr = cfg.get("telem_destaddr")
        self.dstport = cfg.get("telem_destport")
        self.mcast_send_socket = None
        self.initSocket()

    def initSocket(self):
        self.mcast_send_socket = socket.socket(socket.AF_INET,
                socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        #self.mcast_send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    def set_destination(self, multicast_ipaddr):
        self.dstaddr = multicast_ipaddr
        self.initSocket()

    def updateTelem(self, dict_vals):
        for key, val in dict_vals.items():
            with self.socket_lock:
                self.cur_telem[key] = val

    def sendTelemTick(self):
        with self.socket_lock:
            tick_str = ujson.dumps(self.cur_telem)
            self.mcast_send_socket.sendto(tick_str, (self.dstaddr, self.dstport))