#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
import logging
from dataclasses import asdict, dataclass, field, fields
from enum import Enum
from typing import ClassVar, Generic, Optional, Set, Type, TypeVar

from django.utils.encoding import smart_str
from redis import Redis

from apigateway.utils.redis_utils import get_default_redis_client, get_redis_key

logger = logging.getLogger(__name__)


def custom_asdict_factory(data):
    def convert_value(obj):
        if isinstance(obj, Enum):
            return obj.value
        return obj

    return {k: convert_value(v) for k, v in data}


@dataclass
class MeasurementPoint:
    measurement: ClassVar[str]
    name: str
    timestamp: int

    def __post_init__(self):
        if not isinstance(self.name, str):
            self.name = smart_str(self.name)
        if not isinstance(self.timestamp, int):
            self.timestamp = int(self.timestamp)


T = TypeVar("T", bound=MeasurementPoint)


@dataclass
class Measurement(Generic[T]):
    """Measurement is a collection of metrics."""

    point_type: Type[T]
    client: Redis = field(default_factory=get_default_redis_client)
    _available_fields: Set[str] = field(default_factory=set)

    def __post_init__(self):
        self._available_fields.update(i.name for i in fields(self.point_type))

    def _get_key(self, name: str):
        if not self.point_type.measurement:
            return name

        return get_redis_key(f"{self.point_type.measurement}:{name}")

    def update(self, point: T):
        """Update metrics."""
        values = asdict(
            point,
            dict_factory=custom_asdict_factory,
        )

        self.client.hmset(self._get_key(point.name), values)  # type: ignore

    def query(self, name: str) -> Optional[T]:
        """Query metrics."""

        result = self.client.hgetall(self._get_key(name))
        if not result:
            return None

        values = {}
        for key, value in result.items():
            attr = key.decode()
            if attr in self._available_fields:
                values[attr] = value

        return self.point_type(**values)
