import logging

from threading import Thread
from lib.scanner import TCPScanner

logger = logging.getLogger(__name__)


class Worker(Thread):
    def __init__(self, name, host, opened=None, concurrency=None, timeout=None):
        Thread.__init__(self)

        assert concurrency is not None

        self.done = False
        self.name = name
        self.concurrency = concurrency
        self.opened = opened

        scanner_kw = {}
        if timeout is not None:
            scanner_kw['timeout'] = timeout
        self.scanner = TCPScanner(host, range(0, 65535), **scanner_kw)

    def run(self):
        logger.info(f'starting {self.name} ({self.concurrency} threads)')
        self.scanner.scan(num_threads=self.concurrency)
        self.done = not self.scanner.failed
        logger.info(f'finished {self.name}')

    def get_results(self):
        return self.scanner.results

    def is_expected(self, port):
        return (self.opened is not None) and (port in self.opened)

    def get_host(self):
        return self.scanner.host
