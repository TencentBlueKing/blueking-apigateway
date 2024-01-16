# -*- coding: utf-8 -*-
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
from rest_framework import serializers

from apigateway.common.mixins.contexts import GetGatewayFromContextMixin
from apigateway.core.constants import APP_CODE_PATTERN


class MaxCountPerGatewayValidator(GetGatewayFromContextMixin):
    requires_context = True

    def __init__(self, model, max_count_callback, message):
        self.model = model
        self.max_count_callback = max_count_callback
        self.message = message

    def _get_exist_count(self, gateway):
        return self.model.objects.filter(api_id=gateway.id).count()

    def __call__(self, attrs, serializer):
        gateway = self._get_gateway(serializer)
        instance = getattr(serializer, "instance", None)

        if instance:
            # 更新时，不校验
            return

        if self._get_exist_count(gateway) >= self.max_count_callback(gateway):
            message = self.message.format(max_count=self.max_count_callback(gateway))
            raise serializers.ValidationError(message)


class ResourceIDValidator(GetGatewayFromContextMixin):
    requires_context = True

    def __call__(self, value, serializer_field):
        if not value:
            return

        gateway = self._get_gateway(serializer_field)
        resource_ids = value
        if isinstance(value, int):
            resource_ids = [value]

        assert isinstance(resource_ids, list)

        from apigateway.core.models import Resource

        count = Resource.objects.filter(api_id=gateway.id, id__in=resource_ids).count()
        if count != len(set(resource_ids)):
            raise serializers.ValidationError(_("网关【id={api_id}】下指定的部分资源ID不存在。").format(api_id=gateway.id))


class ReservedAPINameValidator:
    """保留的网关名校验，开源版网关名不能以 'bk-' 开头"""

    def __call__(self, value: str):
        if not (
            getattr(settings, "CHECK_RESERVED_GATEWAY_NAME", False)
            and getattr(settings, "RESERVED_GATEWAY_NAME_PREFIXES", None)
        ):
            return

        for prefix in settings.RESERVED_GATEWAY_NAME_PREFIXES:
            if value.startswith(prefix):
                raise serializers.ValidationError(_("网关名不能以【{prefix}】开头，其为官方保留字。").format(prefix=prefix))


class NameValidator:
    """currently:
    - gateway_name can be endswith '-'
    - stage name can be endswith '-' and '_'
    - resource name can be endswith '-'
    while build the key/name of etcd/helm/sdk, the '-'/'_' will be striped,
    it would cause some problem if a-/a convert to the same key/name,
    so, we check the name while creating gateway/stage/resource

    since: 2024-01-16, make standardization
    """

    def __call__(self, value: str):
        if value.endswith("-"):
            raise serializers.ValidationError(_("名称不能以【-】结尾。"))

        if value.endswith("_"):
            raise serializers.ValidationError(_("名称不能以【_】结尾。"))


class BKAppCodeValidator:
    def __call__(self, value):
        if not value:
            return

        assert isinstance(value, str)

        if not APP_CODE_PATTERN.match(value):
            raise serializers.ValidationError(_("蓝鲸应用【{value}】不匹配要求的模式。").format(value=value))


class BKAppCodeListValidator:
    def __call__(self, value):
        if not value:
            return

        assert isinstance(value, list)

        invalid_app_codes = [app_code for app_code in value if not APP_CODE_PATTERN.match(app_code)]
        if invalid_app_codes:
            raise serializers.ValidationError(
                _("蓝鲸应用【{app_codes}】不匹配要求的模式。").format(app_codes=", ".join(sorted(invalid_app_codes)))
            )