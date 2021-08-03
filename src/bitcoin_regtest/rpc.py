import decimal
import json
from typing import Any, Callable

import requests


class BTCJsonRPC:
    """Allows to send any RPC method to BTC backend.

    Usage:
    - one-time connection:
        - response = BTCJsonRPC(...)()
    - reusable object:
        - obj = BTCJsonRPC(...)
        - address = obj.getnewaddress()
        - response = obj.generatetoaddress(101, address)
    """

    def __init__(self, url: str, user: str, passwd: str, method: str = "") -> None:
        self.url = url
        self._user = user
        self._passwd = passwd
        self._method_name = method

    def __getattr__(self, method_name: str) -> Callable:
        """Writing obj.method_name returns a callable object performing specified method"""
        return BTCJsonRPC(
            self.url,
            self._user,
            self._passwd,
            method_name,
        )

    def __call__(self, *args) -> Any:
        rpc_playload = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": self._method_name,
                "params": args,
            }
        )
        headers = {"Content-type": "application/json"}
        r = requests.post(
            self.url,
            headers=headers,
            data=rpc_playload,
            auth=(self._user, self._passwd),
        )
        resp = r.json(parse_float=decimal.Decimal)

        if resp.get("error") is not None:
            e = resp["error"]
            raise Exception(f"Received error: {e['code']}:{e['message']}")

        return resp["result"]
