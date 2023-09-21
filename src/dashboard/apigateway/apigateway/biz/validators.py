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
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.common.mixins.contexts import GetGatewayFromContextMixin
from apigateway.core.constants import HOST_WITHOUT_SCHEME_PATTERN
from apigateway.core.models import Proxy, Resource, ResourceVersion

from .constants import APP_CODE_PATTERN, STAGE_VAR_FOR_PATH_PATTERN


class MaxCountPerGatewayValidator(GetGatewayFromContextMixin):
    requires_context = True

    def __init__(self, model, max_count_callback, message):
        self.model = model
        self.max_count_callback = max_count_callback
        self.message = message

    def _get_exist_count(self, gateway):
        fields = [f.name for f in self.model._meta.get_fields()]
        return self.model.objects.filter(gateway_id=gateway.id).count()

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

        count = Resource.objects.filter(gateway_id=gateway.id, id__in=resource_ids).count()
        if count != len(set(resource_ids)):
            raise serializers.ValidationError(_("网关【id={gateway_id}】下指定的部分资源ID不存在。").format(gateway_id=gateway.id))


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


class BKAppCodeValidator:
    def __call__(self, value):
        if not value:
            return

        assert isinstance(value, str)

        if not APP_CODE_PATTERN.match(value):
            raise serializers.ValidationError(_("蓝鲸应用【{value}】不匹配要求的模式。").format(value=value))


class StageVarsValuesValidator:
    """
    校验变量的值是否符合要求
    - 用作路径变量时：值应符合路径片段规则
    - 用作Host变量时：值应符合 Host 规则
    """

    def __call__(self, attrs):
        gateway = attrs["gateway"]
        stage_name = attrs["stage_name"]
        stage_vars = attrs["vars"]
        resource_version_id = attrs["resource_version_id"]

        used_stage_vars = ResourceVersion.objects.get_used_stage_vars(gateway.id, resource_version_id)
        if not used_stage_vars:
            return

        for key in used_stage_vars["in_path"]:
            if key not in stage_vars:
                raise serializers.ValidationError(
                    _("环境【{stage_name}】中，环境变量【{key}】在发布版本的资源配置中被用作路径变量，必须存在。").format(stage_name=stage_name, key=key),
                )
            if not STAGE_VAR_FOR_PATH_PATTERN.match(stage_vars[key]):
                raise serializers.ValidationError(
                    _("环境【{stage_name}】中，环境变量【{key}】在发布版本的资源配置中被用作路径变量，变量值不是一个合法的 URL 路径片段。").format(
                        stage_name=stage_name,
                        key=key,
                    ),
                )

        for key in used_stage_vars["in_host"]:
            _value = stage_vars.get(key)
            if not _value:
                raise serializers.ValidationError(
                    _("环境【{stage_name}】中，环境变量【{key}】在发布版本的资源配置中被用作 Host 变量，不能为空。").format(
                        stage_name=stage_name, key=key
                    ),
                )
            if not HOST_WITHOUT_SCHEME_PATTERN.match(_value):
                raise serializers.ValidationError(
                    _('环境【{stage_name}】中，环境变量【{key}】在发布版本的资源配置中被用作 Host 变量，变量值不是一个合法的 Host（不包含"http(s)://"）。').format(
                        stage_name=stage_name,
                        key=key,
                    )
                )


class ResourceVersionValidator:
    """
    资源版本创建时校验网关资源版本(open/api)
    """

    def __call__(self, attrs):

        gateway = attrs["gateway"]

        version = attrs.get("version", attrs.get("name"))  # 兼容一下open

        # 校验网关下资源数量，网关下资源数量为0时，不允许创建网关版本
        if not Resource.objects.filter(gateway_id=gateway.id).exists():
            raise serializers.ValidationError(_("请先创建资源，然后再生成版本。"))

        # 判断是否创建资源
        if not Resource.objects.filter(gateway_id=gateway.id).exists():
            raise serializers.ValidationError(_("请先创建资源，然后再生成版本。"))

        # 是否绑定backend
        if Proxy.objects.filter(resource__gateway=gateway, backend__isnull=True).exists():
            raise serializers.ValidationError(_("存在资源未绑定后端服务. "))

        # ResourceVersion 中数据量较大，因此，不使用 UniqueTogetherValidator
        if ResourceVersion.objects.filter(gateway=gateway, version=version).exists():
            raise serializers.ValidationError(_("版本 {version} 已存在。").format(version=version))
