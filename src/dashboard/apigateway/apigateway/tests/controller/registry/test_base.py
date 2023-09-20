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

from apigateway.controller.registry.base import Registry


class DummyRegistry(Registry):
    registry_type = "dummy"

    def apply_resource(self, resource):
        pass

    def sync_resources_by_key_prefix(self, resources):
        pass

    def delete_resources_by_key_prefix(self):
        pass

    def iter_by_type(self, resource_type):
        pass


class TestRegistry:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.registry = DummyRegistry(key_prefix="/testing")

    @pytest.mark.parametrize(
        "key_prefix, expected",
        [
            ("/testing", "/testing/"),
            ("/testing/", "/testing/"),
        ],
    )
    def test_init(self, key_prefix, expected):
        registry = DummyRegistry(key_prefix=key_prefix)
        assert registry.key_prefix == expected

    def test_get_kind_key_prefix(self, fake_custom_resource):
        result = self.registry._get_kind_key_prefix(fake_custom_resource.kind)
        assert result == f"/testing/{fake_custom_resource.kind}/"

    def test_get_key(self, fake_custom_resource):
        result = self.registry._get_key(fake_custom_resource.kind, fake_custom_resource.metadata.name)
        assert result == f"/testing/{fake_custom_resource.kind}/{fake_custom_resource.metadata.name}"
