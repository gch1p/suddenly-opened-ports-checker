#!/usr/bin/env python3
import logging
import yaml
import math

from pprint import pprint
from argparse import ArgumentParser
from ch1p import telegram_notify
from threading import Thread, Lock
from html import escape
from scanner import TCPScanner, PortState

mutex = Lock()
logger = logging.getLogger(__name__)


class Colored:
    GREEN = '\033[92m'
    RED = '\033[91m'
    END = '\033[0m'


class Results:
    def __init__(self):
        self.warnings = []
        self.mutex = Lock()

    def add(self, worker):
        host = worker.get_host()
        with self.mutex:
            if not worker.done:
                print(f'{Colored.RED}{worker.name}: scanning failed{Colored.END}')
                return

            print(f'{worker.name} ({host}):')

            opened = []
            results = worker.get_results()
            for port, state in results:
                if state != PortState.OPEN:
                    continue

                opened.append(port)
                if not worker.is_expected(port):
                    self.warnings.append(f'<b>{worker.name}</b> ({host}): port {port} is open')
                    print(f'    {Colored.RED}{port} opened{Colored.END}')
                else:
                    print(f'    {Colored.GREEN}{port} opened{Colored.END}')

            if worker.opened:
                for port in worker.opened:
                    if port not in opened:
                        self.warnings.append(
                            f'<b>{worker.name}</b> ({host}): port {port} is NOT open')
                        print(f'    {Colored.RED}{port} not opened{Colored.END}')
            print()

    def has_warnings(self):
        return len(self.warnings) > 0

    def notify(self, chat_id=None, token=None):
        text = '<b>❗️Attention!</b>\n\n'
        text += '\n'.join(self.warnings)

        telegram_notify(text, parse_mode='html', chat_id=chat_id, token=token)


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
        self.done = True
        logger.info(f'finished {self.name}')

    def get_results(self):
        return self.scanner.results

    def is_expected(self, port):
        return (self.opened is not None) and (port in self.opened)

    def get_host(self):
        return self.scanner.host


def main():
    parser = ArgumentParser()
    parser.add_argument('--config', type=str, required=True,
                        help='path to config file in yaml format')
    parser.add_argument('--verbose', action='store_true',
                        help='set logging level to DEBUG')
    parser.add_argument('--concurrency', default=200, type=int,
                        help='default number of threads per target')
    parser.add_argument('--timeout', default=5, type=int,
                        help='default timeout')
    parser.add_argument('--threads-limit', default=0, type=int,
                        help='global threads limit')
    parser.add_argument('--no-telegram', action='store_true',
                        help='just print results, don\'t send to telegram')
    args = parser.parse_args()

    # setup loggign
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=(logging.DEBUG if args.verbose else logging.INFO))

    # load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
        # pprint(config)

    assert isinstance(config, dict)
    assert 'servers' in config
    if not args.no_telegram:
        assert 'telegram' in config

    # let's go
    results = Results()
    max_threads = math.inf if args.threads_limit == 0 else args.threads_limit
    active_threads = 1

    def get_active_threads():
        n = active_threads
        if workers:
            n += workers[0].concurrency
        return n

    workers = []
    for name, data in config['servers'].items():
        w = Worker(name, data['host'], data['opened'],
                   concurrency=int(data['concurrency']) if 'concurrency' in data else args.concurrency,
                   timeout=int(data['timeout']) if 'timeout' in data else args.timeout)
        workers.append(w)

    current_workers = []
    while workers:
        w = workers.pop(0)
        active_threads += w.concurrency+1

        current_workers.append(w)
        w.start()

        while current_workers and get_active_threads() >= max_threads:
            for cw in current_workers:
                cw.join(timeout=0.1)
                if not cw.is_alive():
                    results.add(cw)
                    current_workers.remove(cw)
                    active_threads -= cw.concurrency+1

    for cw in current_workers:
        cw.join()
        results.add(cw)

    if results.has_warnings() and not args.no_telegram:
        results.notify(chat_id=config['telegram']['chat-id'],
                       token=config['telegram']['token'])


if __name__ == '__main__':
    main()
