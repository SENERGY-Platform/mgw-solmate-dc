"""
   Copyright 2022 InfAI (CC SES)

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import json
import typing
from threading import Thread

import mgw_dc.dm

__all__ = ("Solmate",)

import requests
import websocket
from mgw_dc.dm import device_state

from util import get_logger, conf

logger = get_logger(__name__.split(".", 1)[-1])


class Solmate(mgw_dc.dm.Device, Thread):
    def __init__(self, ip: str):
        self._auth = False
        self._credentials = None
        self._ws: typing.Optional[websocket.WebSocketApp] = None
        self.ip = ip
        self._id = 0
        self._authenticated = False
        self._callbacks = {}
        self._credentials = requests.get(f"http://{ip}:{conf.Discovery.http_port}/solmateconfig.json",
                                         timeout=10).json()
        self._credentials["serial_num"] = self._credentials["serial-number"]
        self._credentials["device_id"] = "local_webinterface"
        del (self._credentials["serial-number"])
        id = conf.Discovery.device_id_prefix + self._credentials["serial_num"]
        name = f'Solmate {self._credentials["serial_num"]}'
        state = device_state.online
        type = conf.Senergy.dt_solmate
        super().__init__(id, name, type, state, [])
        Thread.__init__(self)

    def _on_message(self, ws, message):
        logger.debug(f"{self.ip} Message {message}")
        try:
            msg = json.loads(message)
        except json.decoder.JSONDecodeError:
            logger.warning(f"{self.ip} Received malformed response from solmate {message}")
            return
        if "id" not in msg:
            logger.warning(f"{self.ip} Received malformed response from solmate {message}")
            return
        msg_id = msg["id"]
        if msg_id not in self._callbacks:
            logger.warning(f"{self.ip} Received response, but no callback registered for id {msg_id}")
            return
        cb = self._callbacks[msg_id]
        if cb is not None:
            if "data" in msg:
                data = msg["data"]
            else:
                data = None
            try:
                cb(msg_id, data)
            except Exception as error:
                logger.error(f"{self.ip} Error in callback: {error}")
        del (self._callbacks[msg_id])

    def _on_error(self, ws, error):
        logger.error(f"{self.ip} Error {error}")
        mgw_dc.dm.Device.state = device_state.offline
        self._authenticated = False

    def _on_close(self, ws, close_status_code, close_msg):
        logger.warning(f"{self.ip} Closed connection {close_status_code} {close_msg}")
        mgw_dc.dm.Device.state = device_state.offline
        self._authenticated = False

    def _on_open(self, ws):
        logger.info(f"{self.ip} Opened connection")
        mgw_dc.dm.Device.state = device_state.online
        self._id = 0
        self._send_message("authenticate", self._credentials, None)
        self._authenticated = True

    def send_message(self, route: str, data, callback: typing.Optional[typing.Callable]) -> int:
        if self._ws is None or not self._authenticated:
            raise RuntimeError("not connected")
        return self._send_message(route, data, callback)

    def _send_message(self, route: str, data, callback: typing.Optional[typing.Callable]) -> int:
        msg_id = self._id
        self._id = self._id + 1
        self._callbacks[msg_id] = callback
        msg = "{" + f'"id": {msg_id}, "route":"{route}", "data":{json.dumps(data)}' + "}"
        self._ws.send(msg)
        return msg_id

    def run(self) -> None:
        logger.info("starting {} ...".format(self.name))
        while True:
            self._ws = websocket.WebSocketApp(f"ws://{self.ip}:{conf.Discovery.ws_port}",
                                              on_open=self._on_open,
                                              on_message=self._on_message,
                                              on_error=self._on_error,
                                              on_close=self._on_close)
            self._ws.run_forever()
