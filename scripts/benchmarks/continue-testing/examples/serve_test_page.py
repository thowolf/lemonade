#!/usr/bin/env python3
"""Simple static server to serve the Continue test page.
Run this script during E2E tests; it serves files from this `examples` directory on port 8001.
"""
import http.server
import socketserver
import os

PORT = int(os.getenv('CONTINUE_TEST_PORT', '8001'))
DIRECTORY = os.path.dirname(__file__)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

if __name__ == '__main__':
    with socketserver.TCPServer(('127.0.0.1', PORT), Handler) as httpd:
        print(f"Serving on http://127.0.0.1:{PORT}/continue_test_page.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.shutdown()
