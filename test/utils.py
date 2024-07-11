# ICOS Dynamic Policy Manager
# Copyright © 2022-2024 Engineering Ingegneria Informatica S.p.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This work has received funding from the European Union's HORIZON research
# and innovation programme under grant agreement No. 101070177.

from pydantic import TypeAdapter


def get_registry_from_http_client(http_client):
  return http_client.app.routes[0].app.state.polman_registry


def get_storage_from_http_client(http_client):
  return http_client.app.routes[0].app.state.polman_registry._ps

def build(type, d):
  return TypeAdapter(type).validate_python(d)
