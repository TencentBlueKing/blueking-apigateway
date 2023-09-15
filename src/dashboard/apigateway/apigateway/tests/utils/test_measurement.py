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
from dataclasses import dataclass

import pytest

from apigateway.utils.measurement import Measurement, MeasurementPoint


@dataclass
class DemoMeasurementPoint(MeasurementPoint):
    measurement = "testing"
    value: int

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.value, int):
            self.value = int(self.value)


@pytest.fixture
def timestamp():
    return 689745600


@pytest.fixture
def mock_redis(mocker):
    return mocker.MagicMock()


class TestMeasurement:
    def test_update(self, mock_redis, timestamp, settings):
        measurement = Measurement(point_type=DemoMeasurementPoint, client=mock_redis)
        point = DemoMeasurementPoint(name="foo", timestamp=timestamp, value=1)
        measurement.update(point)

        mock_redis.hmset.assert_called_once_with(
            f"{settings.REDIS_PREFIX}{DemoMeasurementPoint.measurement}:foo",
            {
                "timestamp": timestamp,
                "name": point.name,
                "value": point.value,
            },
        )

    def test_query(self, mock_redis, timestamp):
        name = "foo"
        value = 1
        mock_redis.hgetall.return_value = {
            b"timestamp": f"{timestamp}".encode(),
            b"name": name.encode(),
            b"value": f"{value}".encode(),
        }

        measurement = Measurement(point_type=DemoMeasurementPoint, client=mock_redis)
        point = measurement.query(name)
        assert isinstance(point, DemoMeasurementPoint)
        assert point.name == name
        assert point.value == value
        assert point.timestamp == timestamp
