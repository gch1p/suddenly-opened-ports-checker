# suddenly-opened-ports-checker

Python script that scans TCP ports of your servers and notifies you about
unexpected changes (new opened ports, or closed ports expected to be open).

## Usage

Python 3.7 or newer is required.

```
usage: suddenly-opened-ports-checker.py [-h] --config CONFIG [--verbose] [--concurrency CONCURRENCY] [--timeout TIMEOUT] [--threads-limit THREADS_LIMIT] [--no-telegram]

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG       path to config file in yaml format
  --verbose             set logging level to DEBUG (default is INFO)
  --concurrency CONCURRENCY
                        default number of threads per target (defaults to 200)
  --timeout TIMEOUT     default timeout (defaults to 5)
  --threads-limit THREADS_LIMIT
                        global threads limit (default is no limit)
  --no-telegram         just print results, don't send to telegram

```

## Config example

Each server definition must have at least `host` and `opened` keys. `opened` is
a list of ports expected to be open.

You can also set per-server `concurrency` and `timeout`.

```yaml
server-1:
  host: 1.2.3.4
  opened:
    - 22
    - 80
    - 443

server-2:
  host: 5.6.7.8
  opened: []
  concurrency: 1000
  timeout: 2
```

## License

MIT
