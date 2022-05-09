# Trezor-user-env tools

__tools__ directory is a collection of small scripts not used in production, but available for developers working with/on `tenv`.

## [delete_red_square.py](../tools/delete_red_square.py)
- given a picture path as a script argument, deletes the red square from the right top of the picture
- useful for removing the sign of debuglink

## [ws_client.py](../tools/ws_client.py)
- can connect to the local controller/websocket and send it any message with arguments, while receiving and showing the answer
- useful for testing/developing the controller commands
