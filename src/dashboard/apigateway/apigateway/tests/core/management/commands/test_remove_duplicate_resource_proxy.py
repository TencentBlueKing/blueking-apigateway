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
from ddf import G

from apigateway.core.management.commands.remove_duplicate_resource_proxy import Command
from apigateway.core.models import Proxy


class TestCommand:
    def test_handle(self, fake_resource):
        fake_gateway = fake_resource.gateway
        fake_proxy = Proxy.objects.get(resource_id=fake_resource.id)
        fake_resource.proxy_id = fake_proxy.id
        fake_resource.save()

        command = Command()

        command.handle(fake_gateway.name, dry_run=False)
        assert Proxy.objects.filter(resource_id=fake_resource.id).count() == 1

        G(Proxy, resource=fake_resource, type="mock")
        assert Proxy.objects.filter(resource_id=fake_resource.id).count() == 2

        command.handle(fake_gateway.name, dry_run=False)
        assert list(Proxy.objects.filter(resource_id=fake_resource.id).values_list("id", flat=True)) == [fake_proxy.id]
