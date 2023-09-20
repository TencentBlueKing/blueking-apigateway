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
from collections import defaultdict
from typing import Dict, List

from django.conf import settings

from apigateway.iam.constants import ActionEnum, ResourceTypeEnum, UserRoleEnum


class AuthorizationScopes:
    @classmethod
    def get_scopes(cls, role: UserRoleEnum, gateway_id: int, gateway_name: str) -> List[Dict]:
        field_members = ActionEnum.get_field_members()
        action_fields = [field for field in field_members.values() if role.value in field.metadata.get("role", [])]

        resource_type_to_actions = defaultdict(list)
        for field in action_fields:
            if not field.metadata.get("related_resource_type"):
                continue
            resource_type_to_actions[field.metadata["related_resource_type"]].append(field.real_value)

        return [
            {
                "system": settings.BK_IAM_SYSTEM_ID,
                "actions": [{"id": action} for action in actions],
                # 资源拓扑, 资源类型的顺序必须操作注册时的顺序一致
                "resources": [
                    {
                        "system": settings.BK_IAM_SYSTEM_ID,
                        "type": resource_type,
                        "paths": [
                            [
                                {
                                    "system": settings.BK_IAM_SYSTEM_ID,
                                    "type": ResourceTypeEnum.GATEWAY.value,
                                    "id": str(gateway_id),
                                    "name": gateway_name,
                                }
                            ]
                        ],
                    },
                ],
            }
            for resource_type, actions in resource_type_to_actions.items()
        ]
