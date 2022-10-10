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
import threading
import time
from typing import Dict


from util import get_logger, conf, Solmate, diff

__all__ = ("Discovery",)

from util.device_manager import DeviceManager

logger = get_logger(__name__.split(".", 1)[-1])


class Discovery(threading.Thread):
    def __init__(self, device_manager: DeviceManager):
        super().__init__(name="discovery", daemon=True)
        self._device_manager = device_manager

    def get_solmates(self) -> Dict[str, Solmate]:
        logger.info("Starting scan")
        devices: Dict[str, Solmate] = {}
        known_ips = []
        for k, d in self._device_manager.get_devices():
            known_ips = known_ips.append(d.ip)
            devices[k] = d

        for ip in conf.Discovery.ips.split(","):
            if ip in known_ips:
                continue  # DONT RECREATE
            try:
                solmate = Solmate(ip)
                logger.info("Discovered '" + ip)
                solmate.start()
                devices[solmate.id] = solmate
            except Exception as e:
                logger.warning(e)

        logger.info("Discovered " + str(len(devices)) + " solmates")
        return devices

    def _refresh_devices(self):
        try:
            solmates = self.get_solmates()

            stored_devices = self._device_manager.get_devices()

            new_devices, missing_devices, existing_devices = diff(stored_devices, solmates)
            if new_devices:
                for device_id in new_devices:
                    self._device_manager.handle_new_device(solmates[device_id])
            if missing_devices:
                for device_id in missing_devices:
                    self._device_manager.handle_missing_device(stored_devices[device_id])
            if existing_devices:
                for device_id in existing_devices:
                    self._device_manager.handle_existing_device(stored_devices[device_id])
            self._device_manager.set_devices(devices=solmates)



            #self._device_manager.set_devices(devices=solmates)
            #self._device_manager.publish_devices()
        except Exception as ex:
            logger.error("refreshing devices failed - {}".format(ex))

    def run(self) -> None:
        logger.info("starting {} ...".format(self.name))
        self._refresh_devices()
        last_discovery = time.time()
        while True:
            if time.time() - last_discovery > conf.Discovery.scan_delay:
                last_discovery = time.time()
                self._refresh_devices()
            time.sleep(conf.Discovery.scan_delay / 100)  # at most 1 % too late
