#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from django.utils.functional import cached_property

from apigateway.common.factories import SchemaFactory
from apigateway.core.constants import ContextScopeTypeEnum, ContextTypeEnum

from .context import BaseContext


# FIXME: remove it if no legacy release data exists
class StageProxyHTTPContext(BaseContext):
    """Context data related with HTTP proxy in "stage" scope."""

    scope_type = ContextScopeTypeEnum.STAGE.value
    type = ContextTypeEnum.STAGE_PROXY_HTTP.value

    @cached_property
    def schema(self):
        return SchemaFactory().get_context_stage_proxy_http_schema()

    def contain_hosts(self, scope_id: int) -> bool:
        """Check if the config contains any valid host entries. The hosts were set
        to empty by default and require manual setup.

        :param scope_id: The ID of stage.
        :return: Whether the config contains valid host.
        """
        cfg = self.get_config(scope_id, default=None)
        if not cfg:
            return False
        return any(h.get("host") for h in cfg["upstreams"].get("hosts", []))
