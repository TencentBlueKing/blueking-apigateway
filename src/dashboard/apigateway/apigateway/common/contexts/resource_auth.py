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

from typing import Dict, List

from django.utils.functional import cached_property

from apigateway.common.factories import SchemaFactory
from apigateway.core.constants import ContextScopeTypeEnum, ContextTypeEnum

from .context import BaseContext


class ResourceAuthContext(BaseContext):
    scope_type = ContextScopeTypeEnum.RESOURCE.value
    type = ContextTypeEnum.RESOURCE_AUTH.value

    @cached_property
    def schema(self):
        return SchemaFactory().get_context_resource_bkauth_schema()

    def get_resource_id_to_auth_config(self, resource_ids: List[int]) -> Dict[int, dict]:
        return {context.scope_id: context.config for context in self.filter_contexts(resource_ids)}
