#!/usr/bin/env python3

"""
Serves Dashboard at http://localhost:9002 to easily instruct the controller.
"""

import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn

import helpers

IP = "0.0.0.0"
PORT = 9002
HTML_DIR = Path(__file__).parent.parent / "src" / "dashboard"
LOG_COLOR = "yellow"


def log(text: str, color: str = LOG_COLOR) -> None:
    helpers.log(f"DASHBOARD: {text}", color)


class Dashboard(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        kwargs["directory"] = str(HTML_DIR)
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args) -> None:
        """Adds color to make the log clearer."""
        log(
            "%s - - [%s] %s\n"
            % (self.address_string(), self.log_date_time_string(), format % args)
        )

    def end_headers(self):
        self.send_my_headers()
        SimpleHTTPRequestHandler.end_headers(self)

    def send_my_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")


class ThreadingServer(ThreadingMixIn, HTTPServer):
    pass


def start() -> None:
    log(f"Starting Dashboard at: http://{IP}:{PORT}")
    server = ThreadingServer((IP, PORT), Dashboard)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
