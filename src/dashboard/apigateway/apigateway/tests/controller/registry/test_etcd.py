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

from apigateway.controller.registry.etcd import EtcdRegistry
from apigateway.utils.yaml import yaml_dumps


@pytest.fixture()
def mock_etcd_client(mocker):
    return mocker.Mock()


@pytest.fixture()
def cr_yaml(fake_custom_resource):
    return yaml_dumps(fake_custom_resource.dict(by_alias=True))


class TestEtcdRegistry:
    @pytest.fixture(autouse=True)
    def setup(self, mock_etcd_client):
        self.etcd_client = mock_etcd_client
        self.registry = EtcdRegistry(etcd_client=mock_etcd_client, key_prefix="/testing")

    def test_apply_resource(self, fake_custom_resource, cr_yaml):
        self.registry.apply_resource(fake_custom_resource)
        self.etcd_client.put.assert_called_once_with(
            f"/testing/{fake_custom_resource.kind}/{fake_custom_resource.metadata.name}", cr_yaml
        )

    def test_sync_resources_by_key_prefix(self, resource_type, mocker):
        resource_a = resource_type(metadata={"name": "a"}, value="to_be_removed")
        resource_b = resource_type(metadata={"name": "b"}, value="to_be_updated")
        resource_c = resource_type(metadata={"name": "c"}, value="to_be_created")

        mocker.patch.object(
            self.registry,
            "_get_exist_keys_by_key_prefix",
            return_value={
                f"/testing/{resource_type.kind}/a": True,
                f"/testing/{resource_type.kind}/b": True,
            },
        )

        self.registry.sync_resources_by_key_prefix([resource_b, resource_c])

        calls = [
            mocker.call(f"/testing/{resource_type.kind}/b", yaml_dumps(resource_b.dict(by_alias=True))),
            mocker.call(f"/testing/{resource_type.kind}/c", yaml_dumps(resource_c.dict(by_alias=True))),
        ]
        self.etcd_client.put.assert_has_calls(calls)
        self.etcd_client.delete.assert_called_once_with(f"/testing/{resource_type.kind}/a")

    def test_get_exist_keys_by_key_prefix(self, mocker, faker):
        key = faker.pystr()
        self.etcd_client.get_prefix.return_value = [(mocker.Mock(), mocker.Mock(key=key))]

        keys = self.registry._get_exist_keys_by_key_prefix()
        assert keys == {key: True}
        self.etcd_client.get_prefix.assert_called_once_with("/testing/", keys_only=True)

    def test_delete_resources_by_key_prefix(self):
        self.registry.delete_resources_by_key_prefix()
        self.etcd_client.delete_prefix.assert_called_once_with("/testing/")

    def test_iter_by_type(self, mocker, fake_custom_resource, resource_type, cr_yaml):
        self.etcd_client.get_prefix.return_value = [(cr_yaml, mocker.Mock())]

        results = list(self.registry.iter_by_type(resource_type))
        assert len(results) == 1
        assert results[0] == fake_custom_resource

        self.etcd_client.get_prefix.assert_called_once_with(f"/testing/{resource_type.kind}/")

    @pytest.mark.parametrize(
        "safe_mode, will_raise",
        [
            (True, False),
            (False, True),
        ],
    )
    def test_iter_by_type_with_incorrect_data(self, mocker, resource_type, safe_mode, will_raise):
        self.registry.safe_mode = safe_mode
        self.etcd_client.get_prefix.return_value = [("a:incorrect:yaml", mocker.Mock())]

        try:
            result = list(self.registry.iter_by_type(resource_type))
        except Exception:
            assert will_raise
        else:
            assert not will_raise
            assert not result

        self.etcd_client.get_prefix.assert_called_once_with(f"/testing/{resource_type.kind}/")

    def test_remove_by_key(self, faker):
        key = faker.pystr()
        self.registry._delete_by_key(key)
        self.etcd_client.delete.assert_called_once_with(key)
