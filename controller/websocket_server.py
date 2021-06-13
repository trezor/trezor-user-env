# Author: Johan Hanssen Seferidis
# License: MIT

import errno
import logging
import struct
import sys
from base64 import b64encode
from hashlib import sha1
from socket import error as SocketError

from typing import List, Callable, Any

if sys.version_info[0] < 3:
    from SocketServer import ThreadingMixIn, TCPServer, StreamRequestHandler
else:
    from socketserver import ThreadingMixIn, TCPServer, StreamRequestHandler

logger = logging.getLogger(__name__)
logging.basicConfig()

"""
+-+-+-+-+-------+-+-------------+-------------------------------+
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
|     Extended payload length continued, if payload len == 127  |
+ - - - - - - - - - - - - - - - +-------------------------------+
|                     Payload Data continued ...                |
+---------------------------------------------------------------+
"""

FIN = 0x80
OPCODE = 0x0F
MASKED = 0x80
PAYLOAD_LEN = 0x7F
PAYLOAD_LEN_EXT16 = 0x7E
PAYLOAD_LEN_EXT64 = 0x7F

OPCODE_CONTINUATION = 0x0
OPCODE_TEXT = 0x1
OPCODE_BINARY = 0x2
OPCODE_CLOSE_CONN = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA


# -------------------------------- API ---------------------------------


class API:
    def run_forever(self) -> None:
        try:
            logger.info("Listening on port {} for clients..".format(self.port))  # type: ignore
            self.serve_forever()  # type: ignore
        except KeyboardInterrupt:
            self.server_close()  # type: ignore
            logger.info("Server terminated.")
        except Exception as e:
            logger.error(str(e), exc_info=True)
            exit(1)

    def new_client(self, client, server) -> None:
        pass

    def client_left(self, client, server) -> None:
        pass

    def message_received(self, client, server, message: str) -> None:
        pass

    def set_fn_new_client(self, fn: Callable) -> None:
        self.new_client = fn  # type: ignore

    def set_fn_client_left(self, fn: Callable) -> None:
        self.client_left = fn  # type: ignore

    def set_fn_message_received(self, fn: Callable) -> None:
        self.message_received = fn  # type: ignore

    def send_message(self, client, msg: str) -> None:
        self._unicast_(client, msg)  # type: ignore

    def send_message_to_all(self, msg: str) -> None:
        self._multicast_(msg)  # type: ignore


# ------------------------- Implementation -----------------------------


class WebsocketServer(ThreadingMixIn, TCPServer, API):
    """
        A websocket server waiting for clients to connect.

    Args:
        port(int): Port to bind to
        host(str): Hostname or IP to listen for connections. By default 127.0.0.1
            is being used. To accept connections from any client, you should use
            0.0.0.0.
        loglevel: Logging level from logging module to use for logging. By default
            warnings and errors are being logged.

    Properties:
        clients(list): A list of connected clients. A client is a dictionary
            like below.
                {
                 'id'      : id,
                 'handler' : handler,
                 'address' : (addr, port)
                }
    """

    allow_reuse_address = True
    daemon_threads = True  # comment to keep threads alive until finished

    clients: List[dict] = []
    id_counter = 0

    def __init__(
        self, port: int, host: str = "0.0.0.0", loglevel=logging.WARNING
    ) -> None:
        logger.setLevel(loglevel)
        TCPServer.__init__(self, (host, port), WebSocketHandler)
        self.port = self.socket.getsockname()[1]

    def _message_received_(self, handler, msg: str) -> None:
        self.message_received(self.handler_to_client(handler), self, msg)

    def _ping_received_(self, handler, msg: str) -> None:
        handler.send_pong(msg)

    def _pong_received_(self, handler, msg: str) -> None:
        pass

    def _new_client_(self, handler) -> None:
        self.id_counter += 1
        client = {
            "id": self.id_counter,
            "handler": handler,
            "address": handler.client_address,
        }
        self.clients.append(client)
        self.new_client(client, self)

    def _client_left_(self, handler) -> None:
        client = self.handler_to_client(handler)
        self.client_left(client, self)
        if client in self.clients:
            self.clients.remove(client)

    def _unicast_(self, to_client: dict, msg: str) -> None:
        to_client["handler"].send_message(msg)

    def _multicast_(self, msg: str) -> None:
        for client in self.clients:
            self._unicast_(client, msg)

    def handler_to_client(self, handler):
        for client in self.clients:
            if client["handler"] == handler:
                return client


class WebSocketHandler(StreamRequestHandler):
    def __init__(self, socket, addr, server) -> None:
        self.server = server
        StreamRequestHandler.__init__(self, socket, addr, server)

    def setup(self) -> None:
        StreamRequestHandler.setup(self)
        self.keep_alive = True
        self.handshake_done = False
        self.valid_client = False

    def handle(self) -> None:
        logger.info("handle")
        while self.keep_alive:
            if not self.handshake_done:
                self.handshake()
            elif self.valid_client:
                self.read_next_message()

    def read_bytes(self, num: int) -> bytes:
        # python3 gives ordinal of byte directly
        bytes = self.rfile.read(num)
        if sys.version_info[0] < 3:
            return map(ord, bytes)
        else:
            return bytes

    def read_next_message(self) -> None:
        try:
            b1, b2 = self.read_bytes(2)
        except SocketError as e:  # to be replaced with ConnectionResetError for py3
            if e.errno == errno.ECONNRESET:
                logger.info("Client closed connection.")
                print("Error: {}".format(e))
                self.keep_alive = False
                return
            b1, b2 = 0, 0
        except ValueError:
            b1, b2 = 0, 0

        opcode = b1 & OPCODE
        masked = b2 & MASKED
        payload_length = b2 & PAYLOAD_LEN

        if opcode == OPCODE_CLOSE_CONN:
            logger.info("Client asked to close connection.")
            self.keep_alive = False
            return
        if not masked:
            logger.warn("Client must always be masked.")
            self.keep_alive = False
            return
        if opcode == OPCODE_CONTINUATION:
            logger.warn("Continuation frames are not supported.")
            return
        elif opcode == OPCODE_BINARY:
            logger.warn("Binary frames are not supported.")
            return
        elif opcode == OPCODE_TEXT:
            opcode_handler = self.server._message_received_  # type: ignore
        elif opcode == OPCODE_PING:
            opcode_handler = self.server._ping_received_  # type: ignore
        elif opcode == OPCODE_PONG:
            opcode_handler = self.server._pong_received_  # type: ignore
        else:
            logger.warn("Unknown opcode 0x{:x}.".format(opcode))
            self.keep_alive = False
            return

        if payload_length == 126:
            payload_length = struct.unpack(">H", self.rfile.read(2))[0]
        elif payload_length == 127:
            payload_length = struct.unpack(">Q", self.rfile.read(8))[0]

        masks = self.read_bytes(4)
        message_bytes = bytearray()
        for message_byte in self.read_bytes(payload_length):
            message_byte ^= masks[len(message_bytes) % 4]
            message_bytes.append(message_byte)
        opcode_handler(self, message_bytes.decode("utf8"))

    def send_message(self, message: str) -> None:
        self.send_text(message)

    def send_pong(self, message: str) -> None:
        self.send_text(message, OPCODE_PONG)

    def send_text(self, message: Any, opcode=OPCODE_TEXT) -> bool:
        """
        Important: Fragmented(=continuation) messages are not supported since
        their usage cases are limited - when we don't know the payload length.
        """

        # Validate message
        if isinstance(message, bytes):
            # this is slower but ensures we have UTF-8
            message = try_decode_UTF8(message)
            if not message:
                logger.warning("Can't send message, message is not valid UTF-8")
                return False
        elif sys.version_info < (3, 0) and (
            isinstance(message, str) or isinstance(message, unicode)
        ):
            pass
        elif isinstance(message, str):
            pass
        else:
            logger.warning(
                "Can't send message, message has to be a string or bytes. Given type is {}".format(
                    type(message)
                )
            )
            return False

        header = bytearray()
        payload = encode_to_UTF8(message)
        payload_length = len(payload)

        # Normal payload
        if payload_length <= 125:
            header.append(FIN | opcode)
            header.append(payload_length)

        # Extended payload
        elif payload_length >= 126 and payload_length <= 65535:
            header.append(FIN | opcode)
            header.append(PAYLOAD_LEN_EXT16)
            header.extend(struct.pack(">H", payload_length))

        # Huge extended payload
        elif payload_length < 18446744073709551616:
            header.append(FIN | opcode)
            header.append(PAYLOAD_LEN_EXT64)
            header.extend(struct.pack(">Q", payload_length))

        else:
            raise Exception("Message is too big. Consider breaking it into chunks.")
            return False

        self.request.send(header + payload)
        return True

    def read_http_headers(self) -> dict:
        headers = {}
        # first line should be HTTP GET
        http_get = self.rfile.readline().decode().strip()
        assert http_get.upper().startswith("GET")
        # remaining should be headers
        while True:
            header = self.rfile.readline().decode().strip()
            if not header:
                break
            head, value = header.split(":", 1)
            headers[head.lower().strip()] = value.strip()
        return headers

    def handshake(self) -> None:
        headers = self.read_http_headers()

        # allow closed requests and respond with OK status
        # useful for health check using curl
        if "connection" in headers and headers["connection"] == "close":
            self.keep_alive = False
            self.request.send(("HTTP/1.1 200 OK\r\n").encode())
            return

        try:
            assert headers["upgrade"].lower() == "websocket"
        except AssertionError:
            self.keep_alive = False
            return

        try:
            key = headers["sec-websocket-key"]
        except KeyError:
            logger.warning("Client tried to connect but was missing a key")
            self.keep_alive = False
            return

        response = self.make_handshake_response(key)
        self.handshake_done = self.request.send(response.encode())
        self.valid_client = True
        self.server._new_client_(self)  # type: ignore

    @classmethod
    def make_handshake_response(cls, key: str) -> str:
        return (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Accept: {}\r\n"
            "\r\n".format(cls.calculate_response_key(key))
        )

    @classmethod
    def calculate_response_key(cls, key: str) -> str:
        GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        hash = sha1(key.encode() + GUID.encode())
        response_key = b64encode(hash.digest()).strip()
        return response_key.decode("ASCII")

    def finish(self) -> None:
        if self.valid_client:
            self.server._client_left_(self)  # type: ignore


def encode_to_UTF8(data: str) -> bytes:
    try:
        return data.encode("UTF-8")
    except UnicodeEncodeError as e:
        logger.error("Could not encode data to UTF-8 -- {}".format(e))
        return b""
    except Exception as e:
        raise (e)


def try_decode_UTF8(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return ""
    except Exception as e:
        raise (e)
