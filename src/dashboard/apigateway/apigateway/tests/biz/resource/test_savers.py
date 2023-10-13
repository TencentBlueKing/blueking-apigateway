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

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.biz.resource.savers import ResourceProxyDuplicateError, ResourcesSaver
from apigateway.core.constants import ContextScopeTypeEnum, ContextTypeEnum, ProxyTypeEnum
from apigateway.core.models import Backend, Context, Proxy, Resource


class TestResourceSavers:
    def test_save(self, fake_resource, fake_resource_data):
        fake_gateway = fake_resource.gateway

        resource_data_list = [
            fake_resource_data.copy(update={"resource": fake_resource}, deep=True),
            fake_resource_data.copy(update={"name": "foo", "method": "POST", "path": "/foo"}, deep=True),
        ]
        saver = ResourcesSaver(fake_gateway, resource_data_list, "admin")
        result = saver.save()
        assert len(result) == 2
        assert Resource.objects.filter(gateway=fake_gateway).count() == 2
        assert Proxy.objects.filter(resource__gateway=fake_gateway).count() == 2
        assert (
            Context.objects.filter(
                scope_type=ContextScopeTypeEnum.RESOURCE.value,
                type=ContextTypeEnum.RESOURCE_AUTH.value,
            ).count()
            == 2
        )

    def test_save__error(self, fake_resource, fake_resource_data):
        resource_data_list = [
            fake_resource_data.copy(update={"resource": fake_resource}, deep=True),
        ]
        G(
            Proxy,
            resource=fake_resource,
            type=ProxyTypeEnum.MOCK.value,
        )

        saver = ResourcesSaver(fake_resource.gateway, resource_data_list, "admin")
        with pytest.raises(ResourceProxyDuplicateError):
            saver.save()

    def test_save_resources(self, fake_resource, fake_resource_data):
        fake_gateway = fake_resource.gateway

        resource_data_list = [
            fake_resource_data.copy(update={"resource": fake_resource}, deep=True),
            fake_resource_data.copy(update={"name": "foo", "method": "POST", "path": "/foo"}, deep=True),
        ]
        saver = ResourcesSaver(fake_gateway, resource_data_list, "admin")
        result = saver._save_resources()
        assert result is True

    def test_complete_with_resource(self, fake_gateway, fake_resource_data):
        resource_1 = G(Resource, gateway=fake_gateway, name="foo1", method="GET", path="/foo1")
        resource_2 = G(Resource, gateway=fake_gateway, name="foo2", method="POST", path="/foo2")

        resource_data_list = [
            fake_resource_data.copy(update={"resource": resource_1}, deep=True),
            fake_resource_data.copy(update={"name": "foo2", "method": "POST", "path": "/foo2"}, deep=True),
        ]
        saver = ResourcesSaver(fake_gateway, resource_data_list, "admin")
        saver._complete_with_resource()

        assert resource_data_list[0].resource == resource_1
        assert resource_data_list[1].resource == resource_2

    def test_save_proxies(self, fake_gateway, fake_resource_data):
        backend_1 = G(Backend, gateway=fake_gateway)
        backend_2 = G(Backend, gateway=fake_gateway)

        resource_1 = G(Resource, gateway=fake_gateway, name="foo1", method="GET")
        resource_2 = G(Resource, gateway=fake_gateway, name="foo2", method="POST")

        resource_data_list = [
            fake_resource_data.copy(update={"resource": resource_1, "backend": backend_1}, deep=True),
        ]
        saver = ResourcesSaver(fake_gateway, resource_data_list, "admin")
        saver._save_proxies(resource_ids=[resource_1.id])
        assert Proxy.objects.filter(resource__gateway=fake_gateway).count() == 1
        assert Proxy.objects.get(resource=resource_1).backend_id == backend_1.id

        # 测试 proxy backend 是否被更新
        resource_data_list[0].backend = backend_2
        saver._save_proxies(resource_ids=[resource_1.id])
        assert Proxy.objects.get(resource=resource_1).backend_id == backend_2.id

        resource_data_list = [
            fake_resource_data.copy(update={"resource": resource_1}, deep=True),
            fake_resource_data.copy(update={"resource": resource_2}, deep=True),
        ]
        saver = ResourcesSaver(fake_gateway, resource_data_list, "admin")
        saver._save_proxies(resource_ids=[resource_1.id, resource_2.id])
        assert Proxy.objects.filter(resource__gateway=fake_gateway).count() == 2

    def test_save_auth_configs(self, fake_gateway, fake_resource_data):
        resource = G(Resource, gateway=fake_gateway, name="foo")

        resource_data = fake_resource_data.copy(update={"resource": resource}, deep=True)

        saver = ResourcesSaver(fake_gateway, [resource_data], "admin")
        saver._save_auth_configs(resource_ids=[resource.id])
        ctx = Context.objects.get(scope_id=resource.id, scope_type="resource")
        assert ctx.config == {
            "skip_auth_verification": False,
            "auth_verified_required": True,
            "app_verified_required": True,
            "resource_perm_required": True,
        }

        ctx.config = {
            "skip_auth_verification": True,
            "auth_verified_required": False,
            "app_verified_required": True,
            "resource_perm_required": True,
        }
        ctx.save()

        resource_data.auth_config.app_verified_required = False
        saver = ResourcesSaver(fake_gateway, [resource_data], "admin")
        saver._save_auth_configs(resource_ids=[resource.id])
        ctx = Context.objects.get(scope_id=resource.id, scope_type="resource")
        assert ctx.config == {
            "skip_auth_verification": True,
            "auth_verified_required": True,
            "app_verified_required": False,
            "resource_perm_required": True,
        }

    def test_save_resource_labels(self, fake_resource, fake_resource_data):
        fake_gateway = fake_resource.gateway

        label_1 = G(APILabel, gateway=fake_gateway)
        label_2 = G(APILabel, gateway=fake_gateway)

        G(ResourceLabel, api_label=label_1, resource=fake_resource)

        resource_data_list = [
            fake_resource_data.copy(update={"resource": fake_resource, "label_ids": [label_2.id, 0]}, deep=True),
        ]

        saver = ResourcesSaver(fake_gateway, resource_data_list, "admin")
        saver._save_resource_labels(resource_ids=[fake_resource.id])
        assert ResourceLabel.objects.filter(resource__gateway=fake_gateway).count() == 1
        assert ResourceLabel.objects.filter(api_label=label_1).count() == 0
