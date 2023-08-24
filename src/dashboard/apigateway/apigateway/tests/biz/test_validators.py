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

from apigateway.biz.validators import (
    BKAppCodeListValidator,
    BKAppCodeValidator,
    MaxCountPerGatewayValidator,
    ResourceIDValidator,
)
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.models import Gateway, Resource, Stage


class TestMaxCountPerGatewayValidator:
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

    def test_validate(self, fake_gateway):
        stage = G(Stage, gateway=fake_gateway)
        G(Stage, gateway=fake_gateway)

        # 修改
        slz = self.StageSLZ(instance=stage, data={"name": "prod"}, context={"gateway": fake_gateway})
        slz.is_valid(raise_exception=True)

        # 新增
        slz = self.StageSLZ(data={"name": "prod"}, context={"gateway": fake_gateway})
        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)


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

        # 单个资源
        slz = self.ResourceIDSLZ(data={"resource_id": r1.id}, context={"gateway": fake_gateway})
        slz.is_valid(raise_exception=True)

        slz = self.ResourceIDSLZ(data={"resource_id": r3.id}, context={"gateway": fake_gateway})
        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)

        # 多个资源
        slz = self.ResourceIDsSLZ(data={}, context={"gateway": fake_gateway})
        slz.is_valid(raise_exception=True)

        slz = self.ResourceIDsSLZ(data={"resource_ids": [r1.id, r2.id]}, context={"gateway": fake_gateway})
        slz.is_valid(raise_exception=True)

        slz = self.ResourceIDsSLZ(data={"resource_ids": [r1.id, r3.id]}, context={"gateway": fake_gateway})
        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)


class TestBKAppCodeListValidator:
    class RecordSLZ(serializers.Serializer):
        bk_app_code_list = serializers.ListField(child=serializers.CharField(), validators=[BKAppCodeListValidator()])

    def test_validate(self):
        # ok, empty
        slz = self.RecordSLZ(data={"bk_app_code_list": []})
        slz.is_valid(raise_exception=True)

        # ok, has app
        slz = self.RecordSLZ(data={"bk_app_code_list": ["exist-app"]})
        slz.is_valid(raise_exception=True)

        # failed
        slz = self.RecordSLZ(data={"bk_app_code_list": ["invalid#"]})
        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)


class TestBKAppCodeValidator:
    class RecordSLZ(serializers.Serializer):
        bk_app_code = serializers.CharField(validators=[BKAppCodeValidator()], allow_blank=True)

    def test_validate(self):
        # ok, bk_app_code is blank
        slz = self.RecordSLZ(data={"bk_app_code": ""})
        slz.is_valid(raise_exception=True)

        # ok, valid bk_app_code
        slz = self.RecordSLZ(data={"bk_app_code": "exist-app"})
        slz.is_valid(raise_exception=True)

        # failed, invalid bk_app_code
        slz = self.RecordSLZ(data={"bk_app_code": "invalid#"})
        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)
