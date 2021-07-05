#!/usr/bin/env python3

"""
HTTPServer used as proxy for trezord calls from the outside of docker container
This is workaround for original ip not beeing passed to the container. https://github.com/docker/for-mac/issues/180
Listening on port 21326 and routes requests to the trezord with changed Origin header
"""

import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import requests
from termcolor import colored

TREZORD_HOST = "0.0.0.0:21325"
HEADERS = {
    "Host": TREZORD_HOST,
    "Origin": "https://user-env.trezor.io",
}
IP = "0.0.0.0"
PORT = 21326
SERVER = None
LOG_COLOR = "green"


# POST request headers override
# origin is set to the actual machine that made the call not localhost
def merge_headers(original: dict) -> dict:
    headers = original.copy()
    headers.update(HEADERS)
    return headers


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        try:
            if self.path == "/status/":
                # read trezord status page
                url = f"http://{TREZORD_HOST}{self.path}"
                resp = requests.get(url)

                self.send_response(resp.status_code)
                self.send_resp_headers(resp)
                self.wfile.write(resp.content)
        except Exception as e:
            self.send_error(404, f"Error trying to proxy: {self.path} Error: {e}")

    def do_POST(self, body: bool = True) -> None:
        try:
            url = f"http://{TREZORD_HOST}{self.path}"
            data_len = int(self.headers.get("content-length", 0))
            data = self.rfile.read(data_len)
            headers = merge_headers(dict(self.headers))

            resp = requests.post(url, data=data, headers=headers)

            self.send_response(resp.status_code)
            self.send_resp_headers(resp)
            if body:
                self.wfile.write(resp.content)
        except Exception as e:
            self.send_error(404, f"Error trying to proxy: {self.path} Error: {e}")

    def send_resp_headers(self, resp) -> None:
        # response Access-Control header needs to be exact with original request from the caller
        self.send_header(
            "Access-Control-Allow-Origin",
            self.headers.get("Access-Control-Allow-Origin", "*"),
        )

        # remove Access-Control and Transfer-Encoding headers from the original trezord response
        h = dict(resp.headers)
        h.pop(
            "Transfer-Encoding", "chunked"
        )  # this header returns empty response to the caller (trezor-link)
        h.pop("Access-Control-Allow-Origin", None)
        for key, value in h.items():
            self.send_header(key, value)
        self.end_headers()

    def log_message(self, format, *args) -> None:
        """Adds color to make the log clearer."""
        sys.stderr.write(
            colored(
                "BRIDGE PROXY: %s - - [%s] %s\n"
                % (self.address_string(), self.log_date_time_string(), format % args),
                LOG_COLOR,
            )
        )


class ThreadingServer(ThreadingMixIn, HTTPServer):
    pass


def start() -> None:
    print(
        colored(
            f"BRIDGE PROXY: Starting at {IP}:{PORT}. All requests will be forwarded to Bridge.",
            LOG_COLOR,
        )
    )
    global SERVER
    if SERVER is not None:
        raise RuntimeError("Bridge proxy is already initialized, cannot be run again")
    SERVER = ThreadingServer((IP, PORT), Handler)
    SERVER.daemon_threads = True
    thread = threading.Thread(target=SERVER.serve_forever)
    thread.daemon = True
    thread.start()


def stop(cleanup: bool = False) -> None:
    print(colored("BRIDGE PROXY: Stopping", LOG_COLOR))
    global SERVER
    if SERVER is None:
        if not cleanup:
            raise RuntimeError("Bridge proxy is not running, cannot be stopped")
    else:
        SERVER.shutdown()
        SERVER = None
