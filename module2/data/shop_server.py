"""Serve the simulated shop on http://localhost:8000/ with one rule a static host cannot apply: a rate limit.

    python3 shop_server.py            (run it in the folder that holds shop/)

A client that sends more than 4 requests within one second gets 429 Too Many Requests with a Retry-After header.
Every request is appended to access.log as: time, status, path, User-Agent.
"""
import http.server, os, sys, time, collections, functools

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, 'shop')
LIMIT, WINDOW, RETRY_AFTER = 4, 1.0, 1
seen = collections.defaultdict(collections.deque)        # client address -> times of its recent requests
LOG = os.path.join(HERE, 'access.log')

class Shop(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      '.html': 'text/html; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
                      '.json': 'application/json; charset=utf-8'}

    def do_GET(self):
        now = time.monotonic(); q = seen[self.client_address[0]]
        while q and now - q[0] > WINDOW:
            q.popleft()
        if len(q) >= LIMIT:
            body = b'{"error": "too many requests"}'
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Retry-After', str(RETRY_AFTER))
            self.send_header('Content-Length', str(len(body)))
            self.end_headers(); self.wfile.write(body)
            return
        q.append(now)
        super().do_GET()

    def log_message(self, fmt, *args):
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(f'{time.strftime("%H:%M:%S")} {args[1] if len(args) > 1 else "-"} {self.path} '
                    f'{self.headers.get("User-Agent", "-")}\n')

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = functools.partial(Shop, directory=ROOT)
    with http.server.ThreadingHTTPServer(('127.0.0.1', port), handler) as srv:
        print(f'shop on http://localhost:{port}/  (limit {LIMIT} requests per {WINDOW:g} s)')
        srv.serve_forever()
