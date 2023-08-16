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
from unittest import mock

import pytest
from ddf import G
from django.test import TestCase
from rest_framework import serializers

from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.models import Gateway, Resource, Stage
from apigateway.core.validators import (
    BKAppCodeListValidator,
    BKAppCodeValidator,
    MaxCountPerGatewayValidator,
    ResourceIDValidator,
)
from apigateway.tests.utils.testing import create_request

pytestmark = pytest.mark.django_db


class TestMaxCountPerAPIValidator(TestCase):
    class StageSLZ(serializers.ModelSerializer):
        api = serializers.HiddenField(default=CurrentGatewayDefault())
        name = serializers.CharField()

        class Meta:
            model = Stage
            fields = (
                "api",
                "name",
            )

            validators = [
                MaxCountPerGatewayValidator(
                    Stage,
                    max_count_callback=lambda gateway: 2,
                    message="每个网关最多创建 {max_count} 个环境",
                ),
            ]

    def test_validate(self):
        gateway = G(Gateway)
        request = create_request()
        request.gateway = gateway
        stage = G(Stage, api=gateway)
        [G(Stage, api=gateway) for i in range(2)]

        data = [
            {
                "instance": None,
                "params": {
                    "name": "prod",
                },
                "will_error": True,
            },
            {
                "instance": stage,
                "params": {
                    "name": "prod",
                },
                "will_error": False,
            },
        ]
        for test in data:
            slz = TestMaxCountPerAPIValidator.StageSLZ(
                instance=test["instance"],
                data=test["params"],
                context={"request": request},
            )
            slz.is_valid()
            if test.get("will_error"):
                self.assertTrue(slz.errors)
            else:
                self.assertFalse(slz.errors)


class TestBKAppCodeValidator(TestCase):
    class RecordSLZ(serializers.Serializer):
        bk_app_code = serializers.CharField(validators=[BKAppCodeValidator()], allow_blank=True)

    def test_validate(self):
        data = [
            # ok, bk_app_code is blank
            {
                "params": {
                    "bk_app_code": "",
                },
                "will_error": False,
            },
            # ok, valid bk_app_code
            {
                "params": {
                    "bk_app_code": "exist-app",
                },
                "will_error": False,
            },
            # invalid bk_app_code
            {
                "params": {
                    "bk_app_code": "invalid#",
                },
                "will_error": True,
            },
        ]
        for test in data:
            slz = TestBKAppCodeValidator.RecordSLZ(data=test["params"])
            slz.is_valid()
            if test.get("will_error"):
                self.assertTrue(slz.errors)
            else:
                self.assertFalse(slz.errors)


class TestBKAppCodeListValidator(TestCase):
    class RecordSLZ(serializers.Serializer):
        bk_app_code_list = serializers.ListField(child=serializers.CharField(), validators=[BKAppCodeListValidator()])

    def test_validate(self):
        data = [
            # ok, empty data
            {
                "params": {
                    "bk_app_code_list": [],
                },
                "will_error": False,
            },
            # ok, valid
            {
                "params": {
                    "bk_app_code_list": ["exist-app"],
                },
                "will_error": False,
            },
            # invalid app_code
            {
                "params": {
                    "bk_app_code_list": ["invalid#"],
                },
                "mock": {},
                "will_error": True,
            },
        ]
        for test in data:
            slz = TestBKAppCodeListValidator.RecordSLZ(data=test["params"])
            slz.is_valid()
            if test.get("will_error"):
                self.assertTrue(slz.errors)
            else:
                self.assertFalse(slz.errors)


class TestResourceIDValidator:
    class ResourceIDSLZ(serializers.Serializer):
        resource_id = serializers.IntegerField(validators=[ResourceIDValidator()], allow_null=True, required=False)

    class ResourceIDsSLZ(serializers.Serializer):
        resource_ids = serializers.ListField(
            child=serializers.IntegerField(),
            validators=[ResourceIDValidator()],
            allow_empty=True,
            required=False,
        )

    def test_validate(self, fake_gateway):
        r1 = G(Resource, api=fake_gateway)
        r2 = G(Resource, api=fake_gateway)
        r3 = G(Resource, api=G(Gateway))

        data = [
            {
                "model": self.ResourceIDSLZ,
                "params": {
                    "resource_id": r1.id,
                },
                "will_error": False,
            },
            {
                "model": self.ResourceIDSLZ,
                "params": {
                    "resource_id": r3.id,
                },
                "will_error": True,
            },
            {
                "model": self.ResourceIDsSLZ,
                "params": {
                    "resource_ids": [r1.id, r2.id],
                },
                "will_error": False,
            },
            {
                "model": self.ResourceIDsSLZ,
                "params": {
                    "resource_ids": [r1.id, r3.id],
                },
                "will_error": True,
            },
            {
                "model": self.ResourceIDsSLZ,
                "params": {},
                "will_error": False,
            },
        ]
        for test in data:
            slz = test["model"](
                data=test["params"],
                context={
                    "request": mock.MagicMock(gateway=fake_gateway),
                },
            )
            slz.is_valid()
            if test["will_error"]:
                assert slz.errors
            else:
                assert not slz.errors
