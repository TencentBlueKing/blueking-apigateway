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

from apigateway.apps.esb.bkcore.models import ComponentResourceBinding
from apigateway.biz.esb.component_resource_binding import ComponentResourceBindingHandler
from apigateway.core.models import Resource


class TestComponentResourceBindingHandler:
    def test_sync(self, fake_resource_data):
        resource_1 = G(Resource)
        resource_2 = G(Resource)
        resource_3 = G(Resource)

        G(ComponentResourceBinding, resource_id=resource_1.id, component_id=1)
        G(ComponentResourceBinding, resource_id=resource_2.id, component_id=2)

        resource_data_list = [
            fake_resource_data.copy(
                update={
                    "resource": resource_2,
                    "metadata": {"component_id": 12, "component_method": "GET", "component_path": "/foo"},
                },
                deep=True,
            ),
            fake_resource_data.copy(
                update={
                    "resource": resource_3,
                    "metadata": {"component_id": 13, "component_method": "GET", "component_path": "/bar"},
                },
                deep=True,
            ),
        ]
        ComponentResourceBindingHandler.sync(resource_data_list)

        result = ComponentResourceBinding.objects.filter(
            resource_id__in=[resource_1.id, resource_2.id, resource_3.id]
        ).values_list("component_id", flat=True)
        assert set(result) == {12, 13}
