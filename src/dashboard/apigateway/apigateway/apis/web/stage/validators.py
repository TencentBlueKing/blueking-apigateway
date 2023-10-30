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

from apigateway.biz.released_resource import ReleasedResourceHandler
from apigateway.biz.validators import StageVarsValuesValidator
from apigateway.common.mixins.contexts import GetGatewayFromContextMixin

from .constants import STAGE_VAR_NAME_PATTERN


class StageVarsValidator(GetGatewayFromContextMixin):
    """
    Stage Serializer 中校验 vars 变量
    """

    requires_context = True

    def __call__(self, attrs: dict, serializer):
        gateway = self._get_gateway(serializer)
        instance = getattr(serializer, "instance", None)

        self._validate_vars_keys(attrs["vars"])
        self._validate_vars_values(attrs["vars"], gateway, instance)

    def _validate_vars_keys(self, _vars: dict):
        """
        校验变量的 key 是否符合正则表达式
        """
        for key in _vars:
            if not STAGE_VAR_NAME_PATTERN.match(key):
                raise serializers.ValidationError(
                    _(
                        "变量名【{key}】非法，应由字母、数字、下划线（_）组成，首字符必须是字母，长度小于50个字符。"
                    ).format(key=key),
                )

    def _validate_vars_values(self, _vars: dict, gateway, instance):
        """
        校验变量的值是否符合要求
        - 用作路径变量时：值应符合路径片段规则
        - 用作Host变量时：值应符合 Host 规则
        """
        if not instance:
            return

        stage_id = instance.id
        stage_release = ReleasedResourceHandler.get_stage_release(gateway, [stage_id]).get(stage_id)
        if not stage_release:
            return

        validator = StageVarsValuesValidator()
        validator(
            {
                "gateway": gateway,
                "stage_name": instance.name,
                "vars": _vars,
                "resource_version_id": stage_release["resource_version_id"],
            }
        )
