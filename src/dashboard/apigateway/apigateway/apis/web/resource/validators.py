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
from typing import List, Tuple

from blue_krill.cubing_case import shortcuts
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.core.models import Resource, Stage
from apigateway.utils.list import get_duplicate_items

from .constants import NORMAL_PATH_VAR_NAME_PATTERN, PATH_VAR_PATTERN, STAGE_PATH_VAR_NAME_PATTERN


class LowerDashCaseNameDuplicationValidator:
    requires_context = True

    def __call__(self, attrs, serializer):
        origin_name = attrs.get("name")
        lower_name = shortcuts.to_lower_dash_case(origin_name)
        instance = getattr(serializer, "instance", None)
        gateway = attrs.get("gateway", None)
        if not gateway:
            return

        name_list = Resource.objects.filter(gateway=gateway).values_list("name", flat=True)
        if instance:
            name_list = name_list.exclude(id=instance.id)

        # 校验资源名称是否重复
        for n in name_list:
            if lower_name == shortcuts.to_lower_dash_case(n):
                raise serializers.ValidationError(
                    _(
                        "网关下资源名称 {origin_name} 或其同名驼峰名称已被占用（如 get_foo 会与 getFoo 冲突），请使用其他命名，建议使用统一的命名格式。"
                    ).format(origin_name=origin_name)
                )


class PathVarsValidator:
    def __call__(self, attrs):
        path = attrs.get("path")
        if not path:
            return

        var_names = PATH_VAR_PATTERN.findall(path)
        if not var_names:
            return

        # 校验变量名是否满足正则
        for var_name in var_names:
            if not NORMAL_PATH_VAR_NAME_PATTERN.match(var_name):
                raise serializers.ValidationError(
                    _("前端请求路径 {path} 中的路径变量 {var_name} 不符合规则。").format(path=path, var_name=var_name),
                )

        # 校验变量名是否重复
        duplicate_names = get_duplicate_items(var_names)
        if duplicate_names:
            raise serializers.ValidationError(
                _("前端请求路径 {path} 中的路径变量 {var_name} 重复。").format(
                    path=path, var_name=", ".join(duplicate_names)
                )
            )


class BackendPathVarsValidator:
    requires_context = True

    def __init__(self, check_stage_vars_exist: bool = False):
        self.check_stage_vars_exist = check_stage_vars_exist

    def __call__(self, attrs, serializer):
        path = attrs.get("path", "")
        backend_path = attrs.get("backend_config", {}).get("path", "")
        if not backend_path:
            return

        stages = serializer.context["stages"]
        normal_path_vars, stage_path_vars = self._parse_backend_path(backend_path)
        self._validate_normal_path_vars(backend_path, normal_path_vars, path)
        self._validate_stage_path_vars(backend_path, stage_path_vars, stages)

    def _parse_backend_path(self, backend_path: str) -> Tuple[List[str], List[str]]:
        """解析后端路径，并将其中的路径变量分为普通路径变量，环境路径变量两类"""
        path_vars = PATH_VAR_PATTERN.findall(backend_path)
        if not path_vars:
            return [], []

        normal_path_vars = []
        stage_path_vars = []
        for var_name in path_vars:
            if NORMAL_PATH_VAR_NAME_PATTERN.match(var_name):
                normal_path_vars.append(var_name)
                continue

            match = STAGE_PATH_VAR_NAME_PATTERN.match(var_name)
            if match:
                stage_path_vars.append(match.group(1))
                continue

            raise serializers.ValidationError(
                _("后端请求路径中的路径变量 {var_name} 不符合规则。").format(var_name=var_name)
            )

        return normal_path_vars, stage_path_vars

    def _validate_normal_path_vars(self, backend_path: str, normal_path_vars: List[str], path: str):
        if not normal_path_vars:
            return

        # 后端请求地址中的路径变量，在前端请求地址中必须存在
        not_exist_vars = list(set(normal_path_vars) - set(PATH_VAR_PATTERN.findall(path)))
        if not_exist_vars:
            raise serializers.ValidationError(
                _("后端请求路径 {backend_path} 中的路径变量 {var_name} 在前端请求路径 {path} 中不存在。").format(
                    backend_path=backend_path, var_name=", ".join(not_exist_vars), path=path
                ),
            )

    def _validate_stage_path_vars(self, backend_path: str, stage_path_vars: List[str], stages: List[Stage]):
        if not (self.check_stage_vars_exist and stage_path_vars):
            return

        for stage in stages:
            # 后端路径中路径变量 {env.var_name}，在各网关环境中需存在
            not_exist_vars = list(set(stage_path_vars) - set(stage.vars.keys()))
            if not_exist_vars:
                raise serializers.ValidationError(
                    _("后端请求路径 {backend_path} 中的路径变量 {var_name} 在网关环境 {stage_name} 中不存在。").format(
                        backend_path=backend_path,
                        var_name=", ".join(not_exist_vars),
                        stage_name=stage.name,
                    )
                )
