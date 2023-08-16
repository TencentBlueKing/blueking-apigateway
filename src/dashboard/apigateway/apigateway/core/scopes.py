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
"""
策略、Context 绑定对象 scopes 处理
"""
from abc import ABCMeta, abstractmethod
from typing import List, Optional

from apigateway.common.error_codes import error_codes
from apigateway.core.constants import ScopeTypeEnum
from apigateway.core.models import Stage


class ScopeManager(metaclass=ABCMeta):
    @classmethod
    def get_manager(cls, scope_type: str):
        if scope_type == ScopeTypeEnum.STAGE.value:
            return StageScopeManager()

        raise error_codes.INVALID_ARGUMENT.format(f"unsupported scope_type: {scope_type}")

    @abstractmethod
    def get_scope_ids(self, gateway_id: int, scopes: Optional[list]) -> List[int]:
        pass


class StageScopeManager(ScopeManager):
    def get_scope_ids(self, gateway_id: int, scopes: Optional[list]) -> List[int]:
        """
        :param scopes: 指定范围的数据，eg: [{"name": "prod"}]

        如果未指定 scopes，则返回网关下所有环境ID
        """
        if not scopes:
            return Stage.objects.get_ids(gateway_id)

        stage_names = [scope["name"] for scope in scopes]
        return list(Stage.objects.filter(api_id=gateway_id, name__in=stage_names).values_list("id", flat=True))
