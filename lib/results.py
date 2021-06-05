from threading import Lock
from lib.util import Colored
from lib.scanner import PortState
from ch1p import telegram_notify


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

            if worker.name != host:
                print(f'{worker.name} ({host}):')
            else:
                print(f'{host}:')

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
