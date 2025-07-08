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

from typing import Set

from django.utils.translation import gettext as _

from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.error_codes import error_codes
from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Release


def get_valid_resource_names(gateway_id: int, stage_id: int) -> Set[str]:
    release = Release.objects.filter(
        gateway_id=gateway_id,
        stage_id=stage_id,
        stage__status=StageStatusEnum.ACTIVE.value,
    ).first()
    if not release:
        raise error_codes.FAILED_PRECONDITION.format(
            _("环境已下架或者未发布，请先发布资源到该环境，再更新 MCPServer。"), replace=True
        )
    return ResourceVersionHandler.get_resource_names_set(release.resource_version.id)
