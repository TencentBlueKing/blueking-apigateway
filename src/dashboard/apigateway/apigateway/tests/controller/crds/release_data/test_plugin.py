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
import pytest
from ddf import G

from apigateway.apps.plugin.models import PluginConfig
from apigateway.controller.crds.release_data.plugin import HeaderWriteConvertor
from apigateway.utils.yaml import yaml_dumps


class TestHeaderWriteConvertor:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.convertor = HeaderWriteConvertor()

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {"set": [{"key": "key1", "value": "value1"}], "remove": [{"key": "key2"}]},
                {"set": {"key1": "value1"}, "remove": ["key2"]},
            ),
        ],
    )
    def test_convert(self, data, expected):
        G(PluginConfig, id=1, yaml=yaml_dumps(data))

        config = self.convertor.convert(PluginConfig.objects.get(id=1))
        assert config == expected
