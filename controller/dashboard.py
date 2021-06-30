#!/usr/bin/env python3

"""
Serves Dashboard at http://localhost:9002 to easily instruct the controller.
"""

import sys
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn

from termcolor import colored

IP = "0.0.0.0"
PORT = 9002
HTML = Path(__file__).parent.parent / "controller" / "html"
COLOR = "yellow"


class Dashboard(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        kwargs["directory"] = str(HTML)
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args) -> None:
        """Adds color to make the log clearer."""
        sys.stderr.write(
            colored(
                "DASHBOARD: %s - - [%s] %s\n"
                % (self.address_string(), self.log_date_time_string(), format % args),
                COLOR,
            )
        )


class ThreadingServer(ThreadingMixIn, HTTPServer):
    pass


def start() -> None:
    print(colored(f"DASHBOARD: Starting Dashboard at: http://{IP}:{PORT}", COLOR))
    server = ThreadingServer((IP, PORT), Dashboard)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
