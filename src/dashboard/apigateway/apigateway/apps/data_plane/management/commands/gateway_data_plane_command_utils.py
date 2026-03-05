#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
import json
from pathlib import Path
from typing import List

from django.core.management.base import CommandError
from django.utils.timezone import now


def parse_comma_separated_names(raw_names: str) -> List[str]:
    if not raw_names:
        return []

    seen = set()
    names: List[str] = []
    for item in raw_names.split(","):
        name = item.strip()
        if not name or name in seen:
            continue
        names.append(name)
        seen.add(name)

    return names


def parse_names_from_file(names_file: str, arg_name: str) -> List[str]:
    if not names_file:
        return []

    path = Path(names_file)
    if not path.exists() or not path.is_file():
        raise CommandError(f"{arg_name} does not exist: {names_file}")

    try:
        raw_items = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    except OSError as err:
        raise CommandError(f"failed to read {arg_name}: {names_file}, error: {err}") from err

    seen = set()
    names: List[str] = []
    for item in raw_items:
        if not item or item in seen:
            continue
        names.append(item)
        seen.add(item)

    return names


def parse_gateway_names(gateway_names: str, gateway_names_file: str) -> List[str]:
    if bool(gateway_names) == bool(gateway_names_file):
        raise CommandError("exactly one of --gateway-names / --gateway-names-file must be provided")

    raw_items: List[str] = []
    if gateway_names:
        raw_items = parse_comma_separated_names(gateway_names)
    else:
        raw_items = parse_names_from_file(gateway_names_file, "gateway names file")

    seen = set()
    names: List[str] = []
    for item in raw_items:
        if not item or item in seen:
            continue
        names.append(item)
        seen.add(item)

    if not names:
        raise CommandError("no valid gateway names parsed from input")
    return names


class AuditWriter:
    def __init__(self, stdout, log_file: str):
        self.stdout = stdout
        self.log_file = Path(log_file)

    def write(self, action: str, result: str, **details):
        payload = {
            "time": now().isoformat(),
            "action": action,
            "result": result,
            **details,
        }
        line = json.dumps(payload, ensure_ascii=True)
        self.stdout.write(line)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as fp:
            fp.write(f"{line}\n")
