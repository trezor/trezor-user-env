#!/usr/bin/env python3

"""
Serves "controller/index.html" at http://localhost:9002
"""

from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import threading
from termcolor import colored
import sys

IP = "0.0.0.0"
PORT = 9002
CONTROLLER_HTML = Path(__file__).parent.parent / "controller" / "html"
COLOR = "blue"


class Server(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(CONTROLLER_HTML), **kwargs)

    def log_message(self, format, *args):
        """Adds color to make the log clearer."""
        sys.stderr.write(
            colored(
                "CONTROLLER: %s - - [%s] %s\n"
                % (self.address_string(), self.log_date_time_string(), format % args),
                COLOR,
            )
        )


class ThreadingServer(ThreadingMixIn, HTTPServer):
    pass


def start():
    print(colored("CONTROLLER: Starting HTML at: http://{}:{}".format(IP, PORT), COLOR))
    server = ThreadingServer((IP, PORT), Server)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
