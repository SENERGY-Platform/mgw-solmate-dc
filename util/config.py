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

__all__ = ("conf",)

import simple_env_var


@simple_env_var.configuration
class Conf:
    @simple_env_var.section
    class MsgBroker:
        host = "localhost"
        port = 1881

    @simple_env_var.section
    class Logger:
        level = "debug"
        enable_mqtt = False

    @simple_env_var.section
    class Client:
        clean_session = False
        keep_alive = 30
        id = "solmate-dc"

    @simple_env_var.section
    class Discovery:
        scan_delay = 5 * 60
        device_id_prefix = "solmate-"
        ips = "localhost, 127.0.0.1"
        http_port = 80
        ws_port = 9124

    @simple_env_var.section
    class StartDelay:
        enabled = False
        min = 5
        max = 20

    @simple_env_var.section
    class Senergy:
        dt_solmate = "urn:infai:ses:device-type:11fdc793-4b60-40e0-a3fd-e05d1bf5b779"
        events_live_values_seconds = 1
        service_live_values = "live_values"
        events_injection_settings_seconds = 10
        service_injection_settings = "get_injection_settings"

conf = Conf()
