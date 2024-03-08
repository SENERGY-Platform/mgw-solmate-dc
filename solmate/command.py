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
import traceback
import typing

import mgw_dc

from util import get_logger, MQTTClient, conf
from util.device_manager import DeviceManager

logger = get_logger(__name__.split(".", 1)[-1])

__all__ = ("Command",)


class Command:
    def __init__(self, mqtt_client: MQTTClient, device_manager: DeviceManager):
        self.mqtt_client = mqtt_client
        self.device_manager = device_manager
        self._cb_info = {}

    def execute_command(self, device_id: str, service: str, payload: typing.AnyStr, is_event: bool = False):
        command_id = None
        if not is_event:
            payload = json.loads(payload)
            command_id = payload["command_id"]
            if "data" not in payload or len(payload["data"]) == 0:
                payload = {}
            else:
                payload = json.loads(payload["data"])
        else:
            payload = {}
        if device_id not in self.device_manager.get_devices():
            logger.error("device unknown " + device_id)
            return
        device = self.device_manager.get_devices()[device_id]
        try:
            id = device.send_message(service, payload, self.respond)
            self._cb_info[id] = (service, is_event, device_id, command_id)
        except Exception as ex:
            if is_event and str(ex) != "not connected":
                self.mqtt_client.publish("error/device/" + device_id, str(ex), 1)
            elif not is_event:
                logger.error("Command failed: {}".format(ex))
                logger.error(traceback.format_exc())
                self.mqtt_client.publish("error/command/" + command_id, str(ex), 1)
            return

    def respond(self, id: int, result):
        service, is_event, device_id, command_id = self._cb_info[id]
        del (self._cb_info[id])
        if is_event:
            if service == conf.Senergy.service_live_values and 'pv_power' in result and result['pv_power'] >= conf.Senergy.live_values_cap:
                logger.warn(f"Ignoring message since value is above cap (capped at {conf.Senergy.live_values_cap}): { result['pv_power']}")
                return
            response = result
            topic = mgw_dc.com.gen_event_topic(device_id, service)
        else:
            response = {"command_id": command_id}
            if result is not None:
                response["data"] = json.dumps(result).replace("'", "\"")
            topic = mgw_dc.com.gen_response_topic(device_id, service)
        self.mqtt_client.publish(topic, json.dumps(response).replace("'", "\""), 2)
