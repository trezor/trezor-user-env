#!/usr/bin/env python3

"""
    HTTPServer used as proxy for trezord calls from the outside of docker container
    This is workaround for original ip not beeing passed to the container. https://github.com/docker/for-mac/issues/180
    Listening on port 21326 and routes requests to the trezord with changed Origin header
    It's also serving "constoller.html" at the server index: http://localhost:21326/
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import threading
import requests
import os

TREZORD = '0.0.0.0:21325'
HEADERS = {
    'Host': TREZORD,
    'Origin': 'https://user-env.trezor.io',
}

# POST request headers override
# origin is set to the actual machine that made the call not localhost
def merge_headers(original):
    headers = original.copy()
    headers.update(HEADERS)
    return headers

class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.do_GET(body=False)

    def do_GET(self, body=True):
        try:
            # print("GET: Headers: {}".format(self.headers))
            if self.path == '/status/':
                # read trezord status page
                url = 'http://{}{}'.format(TREZORD, self.path)
                resp = requests.get(url)
                sent = True
                print("   Resp: Headers: {}".format(resp.headers))

                self.send_response(resp.status_code)
                self.send_resp_headers(resp)
                self.wfile.write(resp.content)
            else:
                # serve controller.html
                # TODO: use os.path to build req_path properly (like in trezord)
                if self.path == '/':
                    req_path = './index.html'
                else:
                    req_path = os.curdir + os.sep + self.path


                f = open(os.path.join('./controller', req_path), 'rb')

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            return
        except Exception as e:
            self.send_error(404, 'Error trying to proxy: %s Error: %s' % (self.path, e))

    def do_POST(self, body=True):
        try:
            # print("POST: Path: {}".format(self.path))
            # print("POST: Headers: {}".format(self.headers))
            url = 'http://{}{}'.format(TREZORD, self.path)
            content_len = int(self.headers.get('content-length', 0))
            
            data = self.rfile.read(content_len)

            resp = requests.post(url, data=data, headers=merge_headers(dict(self.headers)), verify=False)
            # print("Resp: Headers: {}".format(resp.headers))

            self.send_response(resp.status_code)
            self.send_resp_headers(resp)
            if body:
                self.wfile.write(resp.content)
            return
        except Exception as e:
            self.send_error(404, 'Error trying to proxy: %s Error: %s' % (self.path, e))

    def send_resp_headers(self, resp):
        h = dict(resp.headers)
        access = resp.headers.get('Access-Control-Allow-Origin', None)
        if access is not None:
            h.pop('Access-Control-Allow-Origin', None)
            # Response header override otherwise it points to docker container local ip
            self.send_header('Access-Control-Allow-Origin', '*')
        for key, value in h.items():
            self.send_header(key, value)
        self.end_headers()

class ThreadingServer(ThreadingMixIn, HTTPServer):
    pass

def start():
    httpd = ThreadingServer(('0.0.0.0', 21326), Handler)
    threading.Thread(target=httpd.serve_forever).start()

if __name__ == '__main__':
    start()