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
import pytest
from ddf import G
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.resource.validators import (
    BackendPathVarsValidator,
    LowerDashCaseNameDuplicationValidator,
    PathVarsValidator,
)
from apigateway.core.models import Resource


class FakeNameVarsSLZ(serializers.Serializer):
    name = serializers.CharField(allow_blank=True)
    gateway = serializers.IntegerField()

    class Meta:
        validators = [
            LowerDashCaseNameDuplicationValidator(),
        ]


class FakePathVarsSLZ(serializers.Serializer):
    path = serializers.CharField(allow_blank=True)

    class Meta:
        validators = [
            PathVarsValidator(),
        ]


class FakeBackendPathVarsSLZ(serializers.Serializer):
    path = serializers.CharField(allow_blank=True)
    backend_config = serializers.DictField()

    class Meta:
        validators = [
            BackendPathVarsValidator(),
        ]


class TestNameVarsValidator:
    def test_validate(self, fake_gateway):
        data1 = {"name": "get_response", "gateway": fake_gateway.id}
        slz1 = FakeNameVarsSLZ(data=data1)
        slz1.is_valid(raise_exception=True)
        G(Resource, gateway=fake_gateway, name=data1["name"])

        # 创建
        data2 = {"name": "getResponse", "gateway": fake_gateway.id}
        slz2 = FakeNameVarsSLZ(data=data2)
        with pytest.raises(ValidationError):
            slz2.is_valid(raise_exception=True)
        r2 = G(Resource, gateway=fake_gateway, name=data2["name"])

        # 更新
        data2 = {"name": "getResponse", "gateway": fake_gateway.id}
        slz2 = FakeNameVarsSLZ(instance=r2, data=data2)
        with pytest.raises(ValidationError):
            slz2.is_valid(raise_exception=True)


class TestPathVarsValidator:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {"path": ""},
                None,
            ),
            (
                {"path": "/foo"},
                None,
            ),
            (
                {"path": "/color/{my-color}"},
                ValidationError,
            ),
            (
                {"path": "/color/{color}/{color}"},
                ValidationError,
            ),
        ],
    )
    def test_validate(self, data, expected):
        slz = FakePathVarsSLZ(data=data)

        if expected is None:
            slz.is_valid(raise_exception=True)
            return

        with pytest.raises(expected):
            slz.is_valid(raise_exception=True)


class TestBackendPathVarsValidator:
    @pytest.mark.parametrize(
        "check_stage_vars_exist, data, expected",
        [
            (
                True,
                {
                    "path": "/foo",
                    "backend_config": {"path": ""},
                },
                None,
            ),
            (
                True,
                {
                    "path": "/color/{color}",
                    "backend_config": {"path": "/color/{color}/{env.color}"},
                },
                None,
            ),
            (
                True,
                {
                    "path": "/color/",
                    "backend_config": {"path": "/color/{color}/"},
                },
                ValidationError,
            ),
            (
                True,
                {
                    "path": "/color/",
                    "backend_config": {"path": "/color/{env.not_exist}/"},
                },
                ValidationError,
            ),
            (
                False,
                {
                    "path": "/color/",
                    "backend_config": {"path": "/color/{env.not_exist}/"},
                },
                None,
            ),
        ],
    )
    def test_validate(self, fake_stage, check_stage_vars_exist, data, expected):
        fake_stage.vars = {"color": "blue"}
        fake_stage.save()

        slz = FakeBackendPathVarsSLZ(data=data, context={"stages": [fake_stage]})
        slz.Meta.validators[0].check_stage_vars_exist = check_stage_vars_exist

        if expected is None:
            slz.is_valid(raise_exception=True)
            return

        with pytest.raises(expected):
            slz.is_valid(raise_exception=True)

    @pytest.mark.parametrize(
        "backend_path, expected, error",
        [
            (
                "/color",
                ([], []),
                None,
            ),
            (
                "/color/{color}",
                (["color"], []),
                None,
            ),
            (
                "/color/{color1}/{color2}/{env.color3}/{env.color4}",
                (["color1", "color2"], ["color3", "color4"]),
                None,
            ),
            (
                "/color/{color#}",
                None,
                ValidationError,
            ),
        ],
    )
    def test_parse_backend_path(self, backend_path, expected, error):
        validator = BackendPathVarsValidator()

        if not error:
            assert validator._parse_backend_path(backend_path) == expected
            return

        with pytest.raises(error):
            validator._parse_backend_path(backend_path)

    @pytest.mark.parametrize(
        "normal_path_vars, path, error",
        [
            (
                [],
                "/color",
                None,
            ),
            (
                ["color"],
                "/color/{color}",
                None,
            ),
            (
                ["color"],
                "/color",
                ValidationError,
            ),
        ],
    )
    def test_validate_normal_path_vars(self, normal_path_vars, path, error):
        validator = BackendPathVarsValidator()

        if not error:
            assert validator._validate_normal_path_vars("", normal_path_vars, path) is None
            return

        with pytest.raises(error):
            validator._validate_normal_path_vars("", normal_path_vars, path)

    @pytest.mark.parametrize(
        "check_stage_vars_exist, stage_path_vars, error",
        [
            (
                False,
                ["not_exist"],
                None,
            ),
            (
                True,
                [],
                None,
            ),
            (
                True,
                ["color"],
                None,
            ),
            (
                True,
                ["not_exist"],
                ValidationError,
            ),
        ],
    )
    def test_validate_stage_path_vars(self, fake_stage, check_stage_vars_exist, stage_path_vars, error):
        fake_stage.vars = {"color": "blue"}
        fake_stage.save()

        validator = BackendPathVarsValidator(check_stage_vars_exist)
        if not error:
            assert validator._validate_stage_path_vars("", stage_path_vars, [fake_stage]) is None
            return

        with pytest.raises(error):
            validator._validate_stage_path_vars("", stage_path_vars, [fake_stage])
