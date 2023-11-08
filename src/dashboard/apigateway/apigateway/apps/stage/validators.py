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
from apigateway.core.constants import HOST_WITHOUT_SCHEME_PATTERN, STAGE_VAR_FOR_PATH_PATTERN, STAGE_VAR_NAME_PATTERN
from apigateway.core.models import Release, ResourceVersion


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

        # 允许变量不存在:
        # openapi 同步环境时，存在修改变量名的情况，此时，当前 resource version 中资源引用的变量可能不存在；
        # 针对此场景，允许更新环境，但是将不再触发版本发布
        allow_var_not_exist = attrs.get("allow_var_not_exist", False)

        used_stage_vars = ResourceVersion.objects.get_used_stage_vars(gateway.id, resource_version_id)
        if not used_stage_vars:
            return

        for key in used_stage_vars["in_path"]:
            if key not in stage_vars:
                if allow_var_not_exist:
                    continue

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
                if allow_var_not_exist:
                    continue

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


class StageVarsValidator(GetGatewayFromContextMixin):
    """
    Stage Serializer 中校验 vars 变量
    """

    requires_context = True

    def __call__(self, attrs: dict, serializer):
        gateway = self._get_gateway(serializer)
        instance = getattr(serializer, "instance", None)

        context = getattr(serializer, "context", {})
        allow_var_not_exist = context.get("allow_var_not_exist", False)

        self._validate_vars_keys(attrs["vars"])
        self._validate_vars_values(attrs["vars"], gateway, instance, allow_var_not_exist)

    def _validate_vars_keys(self, _vars: dict):
        """
        校验变量的 key 是否符合正则表达式
        """
        for key in _vars.keys():
            if not STAGE_VAR_NAME_PATTERN.match(key):
                raise serializers.ValidationError(
                    _("变量名【{key}】非法，应由字母、数字、下划线（_）组成，首字符必须是字母，长度小于50个字符。").format(key=key),
                )

    def _validate_vars_values(self, _vars: dict, gateway, instance, allow_var_not_exist: bool):
        """
        校验变量的值是否符合要求
        - 用作路径变量时：值应符合路径片段规则
        - 用作Host变量时：值应符合 Host 规则
        """
        if not instance:
            return

        stage_id = instance.id
        stage_release = Release.objects.get_stage_release(gateway, [stage_id]).get(stage_id)
        if not stage_release:
            return

        validator = StageVarsValuesValidator()
        validator(
            {
                "gateway": gateway,
                "stage_name": instance.name,
                "vars": _vars,
                "resource_version_id": stage_release["resource_version_id"],
                "allow_var_not_exist": allow_var_not_exist,
            }
        )
