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

from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.apps.plugin.models import PluginConfig
from apigateway.controller.crds.release_data.plugin import (
    DefaultPluginConvertor,
    IPRestrictionConvertor,
    PluginConvertorFactory,
)


class TestDefaultPluginConvertor:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.convertor = DefaultPluginConvertor()

    @pytest.mark.parametrize(
        "yaml_, expected",
        [
            (
                "a: 1",
                {"a": 1},
            ),
        ],
    )
    def test_convert(self, yaml_, expected):
        G(PluginConfig, id=1, yaml=yaml_)

        config = self.convertor.convert(PluginConfig.objects.get(id=1))
        assert config == expected


class TestIPRestrictionConvertor:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.convertor = IPRestrictionConvertor()

    @pytest.mark.parametrize(
        "item, expected",
        [
            (
                "1.1.1.1",
                ["1.1.1.1"],
            ),
            (
                "1.1.1.1\n2.2.2.2\n1.1.1.1",
                ["1.1.1.1", "2.2.2.2"],
            ),
            (
                ["1.1.1.1"],
                ["1.1.1.1"],
            ),
            (
                ["1.1.1.1", "2.2.2.2", "1.1.1.1"],
                ["1.1.1.1", "2.2.2.2"],
            ),
        ],
    )
    def test_parse_config_to_ips(self, item, expected):

        ips = self.convertor._parse_config_to_ips(item)
        assert sorted(ips) == sorted(expected)

    @pytest.mark.parametrize(
        "yaml_, expected",
        [
            (
                "whitelist: |-\n 1.1.1.1",
                {"whitelist": ["1.1.1.1"]},
            ),
            (
                "blacklist: |-\n 1.1.1.1",
                {"blacklist": ["1.1.1.1"]},
            ),
        ],
    )
    def test_convert(self, yaml_, expected):
        G(PluginConfig, id=1, yaml=yaml_)

        config = self.convertor.convert(PluginConfig.objects.get(id=1))
        assert config == expected

    @pytest.mark.parametrize(
        "yaml_, expected",
        [
            (
                "a: 1",
                {"a": 1},
            ),
        ],
    )
    def test_convert_error(self, yaml_, expected):
        G(PluginConfig, id=1, yaml=yaml_)

        with pytest.raises(ValueError):
            self.convertor.convert(PluginConfig.objects.get(id=1))


class TestPluginConvertorFactory:
    def test_get_convertor(self):
        convertor = PluginConvertorFactory.get_convertor(PluginTypeCodeEnum.BK_IP_RESTRICTION.value)
        assert isinstance(convertor, IPRestrictionConvertor)

        convertor = PluginConvertorFactory.get_convertor(PluginTypeCodeEnum.BK_RATE_LIMIT.value)
        assert isinstance(convertor, DefaultPluginConvertor)
