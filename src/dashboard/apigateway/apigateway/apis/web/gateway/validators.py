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
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from rest_framework import serializers

from apigateway.components.paas import is_app_code_occupied
from apigateway.core.constants import GatewayKindEnum


class ReservedGatewayNameValidator:
    """保留的网关名校验，开源版网关名不能以 'bk-' 开头"""

    def __call__(self, value: str):
        if not (
            getattr(settings, "CHECK_RESERVED_GATEWAY_NAME", False)
            and getattr(settings, "RESERVED_GATEWAY_NAME_PREFIXES", None)
        ):
            return

        for prefix in settings.RESERVED_GATEWAY_NAME_PREFIXES:
            if value.startswith(prefix):
                raise serializers.ValidationError(
                    _("网关名不能以【{prefix}】开头，其为官方保留字。").format(prefix=prefix)
                )


class ProgrammableGatewayNameValidator:
    """Validator for programmable gateway name"""

    message = gettext_lazy("可编程网关名称对应的蓝鲸应用 ID 已经存在，无法创建关联应用。")

    def __call__(self, attrs):
        if attrs.get("kind") == GatewayKindEnum.PROGRAMMABLE.value:
            name = attrs.get("name", "")
            # check if the name is already occupied on PaaS
            if is_app_code_occupied(name):
                raise serializers.ValidationError(self.message)
