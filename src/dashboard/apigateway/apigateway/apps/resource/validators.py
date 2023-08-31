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
from apigateway.core.constants import (
    NORMAL_PATH_VAR_NAME_PATTERN,
    PATH_VAR_PATTERN,
    STAGE_PATH_VAR_NAME_PATTERN,
    ProxyTypeEnum,
)
from apigateway.core.models import Stage


class PathVarsValidator:
    def __call__(self, attrs):
        path = attrs.get("path")
        if not path:
            return

        var_names = PATH_VAR_PATTERN.findall(path)
        var_name_set = set()

        for var_name in var_names:
            if not NORMAL_PATH_VAR_NAME_PATTERN.match(var_name):
                raise serializers.ValidationError(
                    _("资源请求路径包含的路径变量【{var_name}】非法，应由字母、数字、下划线（_）组成，首字符必须是字母，长度小于30个字符。").format(var_name=var_name),
                )

            # 校验路径是否包含重复的变量名
            if var_name in var_name_set:
                raise serializers.ValidationError(_("资源请求路径包含的路径变量【{var_name}】重复。").format(var_name=var_name))
            var_name_set.add(var_name)


class ProxyPathVarsValidator(GetGatewayFromContextMixin):
    requires_context = True

    def __init__(self, check_stage_vars_exist=False):
        self.check_stage_vars_exist = check_stage_vars_exist

    def __call__(self, attrs, serializer):
        proxy_path = attrs["proxy_configs"].get("http", {}).get("path", "")
        if not (attrs["proxy_type"] == ProxyTypeEnum.HTTP.value and proxy_path):
            return

        proxy_path_vars = PATH_VAR_PATTERN.findall(proxy_path)
        if not proxy_path_vars:
            return

        gateway = self._get_gateway(serializer)
        normal_proxy_path_vars, stage_proxy_path_vars = self._parse_proxy_path_vars(proxy_path_vars)
        self._validate_normal_proxy_path_vars(attrs["path"], normal_proxy_path_vars)
        self._validate_stage_proxy_path_vars(stage_proxy_path_vars, gateway)

    def _parse_proxy_path_vars(self, proxy_path_vars):
        """
        解析路径变量，将其拆分为普通路径变量，环境路径变量两类
        """
        normal_proxy_path_vars = []
        stage_proxy_path_vars = []
        for var_name in proxy_path_vars:
            if NORMAL_PATH_VAR_NAME_PATTERN.match(var_name):
                normal_proxy_path_vars.append(var_name)
                continue

            match = STAGE_PATH_VAR_NAME_PATTERN.match(var_name)
            if match:
                stage_proxy_path_vars.append(match.group(1))
                continue

            raise serializers.ValidationError(_("后端系统接口路径包含的路径变量【{var_name}】非法。").format(var_name=var_name))
        return normal_proxy_path_vars, stage_proxy_path_vars

    def _validate_normal_proxy_path_vars(self, path, normal_proxy_path_vars):
        if not normal_proxy_path_vars:
            return

        path_vars = PATH_VAR_PATTERN.findall(path)
        not_exist_vars = self._get_not_exist_vars(normal_proxy_path_vars, path_vars)
        if not_exist_vars:
            raise serializers.ValidationError(
                _("后端系统接口路径中的路径变量【{var_name}】在资源请求路径中不存在。").format(var_name=not_exist_vars[0]),
            )

    def _validate_stage_proxy_path_vars(self, stage_proxy_path_vars, gateway):
        if not (self.check_stage_vars_exist and stage_proxy_path_vars):
            return

        for stage in Stage.objects.filter(gateway_id=gateway.id):
            not_exist_vars = self._get_not_exist_vars(stage_proxy_path_vars, stage.vars.keys())
            if not_exist_vars:
                raise serializers.ValidationError(
                    _("后端系统接口路径中的环境变量【{var_name}】在环境【{stage_name}】中不存在。").format(
                        var_name=not_exist_vars[0],
                        stage_name=stage.name,
                    )
                )

    def _get_not_exist_vars(self, checked_vars, source_vars):
        return list(set(checked_vars) - set(source_vars))
