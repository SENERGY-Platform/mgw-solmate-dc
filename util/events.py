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

__all__ = ("Events",)

import time
from threading import Thread

import mgw_dc.com
import schedule

from . import conf, Router, DeviceManager
from .logger import get_logger

logger = get_logger(__name__.split(".", 1)[-1])


class Events(Thread):
    def __init__(self, router: Router, device_manager: DeviceManager):
        super().__init__(name="events", daemon=True)
        self.router = router
        self.device_manager = device_manager

    def queue_live_data(self):
        for device in self.device_manager.get_devices().values():
            self.router.route(mgw_dc.com.gen_command_topic(device.id, conf.Senergy.service_live_values), "", True)

    def queue_injection_settings(self):
        for device in self.device_manager.get_devices().values():
            self.router.route(mgw_dc.com.gen_command_topic(device.id, conf.Senergy.service_injection_settings), "", True)

    def run(self) -> None:
        logger.info("Scheduling events....")

        if conf.Senergy.events_live_values_seconds > 0: schedule.every(conf.Senergy.events_live_values_seconds).seconds.do(self.queue_live_data)
        else: logger.info("Disabling events for service " + conf.Senergy.service_live_values)

        if conf.Senergy.events_injection_settings_seconds > 0: schedule.every(conf.Senergy.events_injection_settings_seconds).seconds.do(self.queue_injection_settings)
        else: logger.info("Disabling events for service " + conf.Senergy.service_injection_settings)

        while True:
            schedule.run_pending()
            time.sleep(1)
