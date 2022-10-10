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

__all__ = ("Router",)

import time
import typing
from queue import Queue
from threading import Thread

import mgw_dc

from .logger import get_logger

logger = get_logger(__name__.split(".", 1)[-1])


class Router(Thread):
    def __init__(self, refresh_callback: typing.Callable, command_callback: typing.Callable):
        super().__init__(name="router", daemon=True)
        self.__refresh_callback = refresh_callback
        self.__command_callback = command_callback
        self.tasks = Queue()

    def route(self, topic: str, payload: typing.AnyStr, is_event: bool = False):
        if self.tasks is None:
            logger.error("Queue not initialized")
            return
        try:
            if topic == mgw_dc.dm.gen_refresh_topic():
                self.__refresh_callback()
            else:
                device_id, service = mgw_dc.com.parse_command_topic(topic)
                self.tasks.put_nowait((device_id, service, payload, is_event))

        except Exception as ex:
            logger.error("can't route message - {}\n{}: {}".format(ex, topic, payload))

    def run(self) -> None:
        logger.info("starting {} ...".format(self.name))
        while True:
            try:
                device_id, service, payload, is_event = self.tasks.get()
                self.__command_callback(device_id, service, payload, is_event)
                self.tasks.task_done()
            except Exception as e:
                logger.error(str(e))
            if self.tasks.qsize() == 0:
                time.sleep(0.1)
