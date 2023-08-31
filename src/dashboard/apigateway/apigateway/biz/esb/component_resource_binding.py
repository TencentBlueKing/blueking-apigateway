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
from typing import List

from apigateway.apps.esb.bkcore.models import ComponentResourceBinding
from apigateway.biz.resource.models import ResourceData


class ComponentResourceBindingHandler:
    @staticmethod
    def sync(resource_data_list: List[ResourceData]):
        # 添加 if 条件，为通过 lint 校验
        resource_ids = [resource_data.resource.id for resource_data in resource_data_list if resource_data.resource]

        ComponentResourceBinding.objects.exclude(resource_id__in=resource_ids).delete()

        bindings = {binding.resource_id: binding for binding in ComponentResourceBinding.objects.all()}

        add_binding = []
        update_binding = []
        for resource_data in resource_data_list:
            assert resource_data.resource

            if resource_data.resource.id in bindings:
                binding = bindings[resource_data.resource.id]
                binding.__dict__.update(
                    component_id=resource_data.metadata.get("component_id") or 0,
                    component_method=resource_data.metadata["component_method"],
                    component_path=resource_data.metadata["component_path"],
                )
                update_binding.append(binding)
            else:
                add_binding.append(
                    ComponentResourceBinding(
                        resource_id=resource_data.resource.id,
                        component_id=resource_data.metadata.get("component_id") or 0,
                        component_method=resource_data.metadata["component_method"],
                        component_path=resource_data.metadata["component_path"],
                    )
                )

        if add_binding:
            ComponentResourceBinding.objects.bulk_create(add_binding, batch_size=100)

        if update_binding:
            ComponentResourceBinding.objects.bulk_update(
                update_binding, fields=["component_id", "component_method", "component_path"], batch_size=100
            )
