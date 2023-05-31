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

from apigateway.controller.registry.dict import DictRegistry


class TestDictRegistry:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.registry = DictRegistry(key_prefix="/testing")

    def test_apply_resource(self, fake_custom_resource, resource_type):
        self.registry.apply_resource(fake_custom_resource)

        results = list(self.registry.iter_by_type(resource_type))
        assert len(results) == 1
        assert results[0] == fake_custom_resource
        assert results[0] is not fake_custom_resource

    def test_sync_resources_by_key_prefix(self, resource_type):
        resource_a = resource_type(metadata={"name": "a"}, value="to_be_removed")
        resource_b = resource_type(metadata={"name": "b"}, value="to_be_updated")
        resource_c = resource_type(metadata={"name": "c"}, value="to_be_created")

        self.registry.sync_resources_by_key_prefix([resource_a, resource_b])
        keys = self.registry._get_exist_keys_by_key_prefix()
        assert keys == {
            f"/testing/{resource_type.kind}/a": True,
            f"/testing/{resource_type.kind}/b": True,
        }

        self.registry.sync_resources_by_key_prefix([resource_b, resource_c])
        keys = self.registry._get_exist_keys_by_key_prefix()
        assert keys == {
            f"/testing/{resource_type.kind}/b": True,
            f"/testing/{resource_type.kind}/c": True,
        }

    def test_delete_resource_by_key_prefix(self, fake_custom_resource):
        self.registry.sync_resources_by_key_prefix([fake_custom_resource])
        keys = self.registry._get_exist_keys_by_key_prefix()
        assert len(keys) == 1

        self.registry.delete_resources_by_key_prefix()
        keys = self.registry._get_exist_keys_by_key_prefix()
        assert keys == {}

    def test_iter_by_type(self, faker, fake_custom_resource, resource_type):
        self.registry.sync_resources_by_key_prefix([fake_custom_resource])

        results = list(self.registry.iter_by_type(resource_type))
        assert len(results) == 1
        assert results[0] == fake_custom_resource
        assert results[0] is not fake_custom_resource
