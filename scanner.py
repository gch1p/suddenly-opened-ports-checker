import struct
import socket
import threading
import queue
import logging

from enum import Enum, auto

logger = logging.getLogger(__name__)


class PortState(Enum):
    OPEN = auto()
    CLOSED = auto()
    FILTERED = auto()


class TCPScanner:
    def __init__(self, host, ports, timeout=5):
        self.host = host
        self.ports = ports
        self.timeout = timeout
        self.results = []
        self.q = queue.SimpleQueue()

    def scan(self, num_threads=5):
        for port in self.ports:
            self.q.put(port)

        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=self.run)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        return self.results

    def run(self):
        try:
            while True:
                self._scan(self.q.get(block=False))
        except queue.Empty:
            return

    def _scan(self, port):
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
            conn.settimeout(self.timeout)

            ret = conn.connect_ex((self.host, port))

            # DATA RECEIVED - SYN ACK
            if ret == 0:
                logger.debug('%s:%d - tcp open (SYN-ACK packet)' % (self.host, port))
                self.results.append((port, PortState.OPEN))

            # RST RECEIVED - PORT CLOSED
            elif ret == 111:
                logger.debug('%s:%d - tcp closed (RST packet)' % (self.host, port))
                self.results.append((port, PortState.CLOSED))

            # ERR CODE 11 - TIMEOUT
            elif ret == 11:
                self.results.append((port, PortState.FILTERED))

            else:
                logger.debug('%s:%d - code %d' % (self.host, port, ret))

            conn.close()

        except socket.timeout:
            self.results.append((port, PortState.FILTERED))
