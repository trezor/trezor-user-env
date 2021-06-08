#!/usr/bin/env python3

"""
HTTPServer used as proxy for trezord calls from the outside of docker container
This is workaround for original ip not beeing passed to the container. https://github.com/docker/for-mac/issues/180
Listening on port 21326 and routes requests to the trezord with changed Origin header
It's also serving "controller.html" at the server index: http://localhost:21326/
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import threading
import requests
import os

TREZORD_HOST = "0.0.0.0:21325"
HEADERS = {
    "Host": TREZORD_HOST,
    "Origin": "https://user-env.trezor.io",
}
PROXY_IP = "0.0.0.0"
PROXY_PORT = 21326


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
            # print("GET: Headers: {}".format(self.headers))
            if self.path == "/status/":
                # read trezord status page
                url = "http://{}{}".format(TREZORD_HOST, self.path)
                resp = requests.get(url)
                # print("   Resp: Headers: {}".format(resp.headers))

                self.send_response(resp.status_code)
                self.send_resp_headers(resp)
                self.wfile.write(resp.content)
            else:
                # serve controller.html
                # TODO: use os.path to build req_path properly (like in trezord)
                if self.path == "/":
                    req_path = "./index.html"
                else:
                    req_path = os.curdir + os.sep + self.path

                f = open(os.path.join("./controller", req_path), "rb")

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            return
        except Exception as e:
            self.send_error(404, "Error trying to proxy: {} Error: {}".format(self.path, e))

    def do_POST(self, body: bool = True) -> None:
        try:
            # print("POST Path: {}".format(self.path))
            # print("POST Headers: {}".format(self.headers))
            url = "http://{}{}".format(TREZORD_HOST, self.path)
            data_len = int(self.headers.get("content-length", 0))
            data = self.rfile.read(data_len)
            headers = merge_headers(dict(self.headers))
            # print("POST Modified headers: {}".format(headers))
            # print("POST Data: {}".format(data))

            resp = requests.post(url, data=data, headers=headers)
            # print("POST Resp Headers: {}".format(resp.headers))
            # print("POST Resp Data: {}".format(resp.content))

            self.send_response(resp.status_code)
            self.send_resp_headers(resp)
            if body:
                self.wfile.write(resp.content)
            return
        except Exception as e:
            self.send_error(404, "Error trying to proxy: {} Error: {}".format(self.path, e))

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


class ThreadingServer(ThreadingMixIn, HTTPServer):
    pass


def start() -> threading.Thread:
    httpd = ThreadingServer((PROXY_IP, PROXY_PORT), Handler)
    httpd.daemon_threads = True
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    return thread


if __name__ == "__main__":
    start()
