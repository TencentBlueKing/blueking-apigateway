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
from typing import Any, Dict, List

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.core.models import Resource, Stage


class PluginBindingHandler:
    @staticmethod
    def get_scopes(gateway_id: int, scope_type: PluginBindingScopeEnum, scope_ids: List[int]) -> List[Dict[str, Any]]:
        if scope_type == PluginBindingScopeEnum.STAGE:
            return list(Stage.objects.filter(gateway_id=gateway_id, id__in=scope_ids).values("id", "name"))

        elif scope_type == PluginBindingScopeEnum.RESOURCE:
            return list(Resource.objects.filter(gateway_id=gateway_id, id__in=scope_ids).values("id", "name"))

        raise ValueError(f"unsupported scope_type: {scope_type.value}")
