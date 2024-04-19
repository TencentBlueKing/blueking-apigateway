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
import json

import pytest
from ddf import G
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apigateway.apps.plugin.apps import PluginConfig
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.biz.validators import (
    BKAppCodeListValidator,
    BKAppCodeValidator,
    MaxCountPerGatewayValidator,
    PublishValidator,
    ReleaseValidationError,
    ResourceIDValidator,
    ResourceVersionValidator,
)
from apigateway.common.factories import SchemaFactory
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.constants import GatewayStatusEnum, ProxyTypeEnum
from apigateway.core.models import Backend, BackendConfig, Gateway, Proxy, Resource, ResourceVersion, Stage


class TestMaxCountPerGatewayValidator:
    class StageSLZ(serializers.ModelSerializer):
        gateway = serializers.HiddenField(default=CurrentGatewayDefault())
        name = serializers.CharField()

        class Meta:
            model = Stage
            fields = (
                "gateway",
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
        r1 = G(Resource, gateway=fake_gateway)
        r2 = G(Resource, gateway=fake_gateway)
        r3 = G(Resource, gateway=G(Gateway))

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


class TestResourceVersionValidator:
    def test_validate(self, faker, fake_stage, fake_gateway, fake_resource):
        resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        validator = ResourceVersionValidator()
        with pytest.raises(ValidationError):
            validator(
                {
                    "gateway": fake_gateway,
                    "version": "1.0.0",
                }
            )

        assert (
            validator(
                {
                    "gateway": fake_gateway,
                    "version": "1.0.1",
                }
            )
            is None
        )
        backend2 = G(
            Backend,
            gateway=fake_gateway,
            name=faker.pystr(),
        )

        G(
            BackendConfig,
            gateway=fake_gateway,
            stage=fake_stage,
            backend=backend2,
            config={
                "type": "node",
                "timeout": 30,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 100}],
            },
        )
        G(
            Proxy,
            type=ProxyTypeEnum.MOCK.value,
            resource=fake_resource,
            backend=backend2,
            _config=json.dumps(
                {
                    "method": faker.http_method(),
                    "path": faker.uri_path(),
                    "match_subpath": False,
                    "timeout": faker.random_int(),
                }
            ),
            schema=SchemaFactory().get_proxy_schema(ProxyTypeEnum.HTTP.value),
        )
        with pytest.raises(ValidationError):
            validator(
                {
                    "gateway": fake_gateway,
                    "version": "1.0.0",
                }
            )


class TestPublishValidator:
    def test_validate_gateway_status(self, fake_gateway, fake_stage, fake_backend, fake_resource_version):
        publish_validator = PublishValidator(fake_gateway, fake_stage, fake_resource_version)
        assert publish_validator._validate_gateway_status() is None

        fake_gateway.status = GatewayStatusEnum.INACTIVE.value
        fake_gateway.save()
        with pytest.raises(ReleaseValidationError):
            publish_validator._validate_gateway_status()

    @pytest.mark.parametrize(
        "vars, mock_used_stage_vars, will_error",
        [
            # ok
            (
                {
                    "prefix": "/o",
                    "domain": "bking.com",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                False,
            ),
            # var in path not exist
            (
                {
                    "domain": "bking.com",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                True,
            ),
            # var in path invalid
            (
                {
                    "prefix": "/test/?a=b",
                    "domain": "bking.com",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                True,
            ),
            # var in hosts not exist
            (
                {
                    "prefix": "/test/",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                True,
            ),
            # var in hosts invalid
            (
                {
                    "prefix": "/test/",
                    "domain": "http://bking.com",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                True,
            ),
        ],
    )
    def test_validate_stage_vars(
        self, mocker, fake_gateway, fake_stage, fake_resource_version, vars, mock_used_stage_vars, will_error
    ):
        mocker.patch(
            "apigateway.biz.validators.ResourceVersionHandler.get_used_stage_vars",
            return_value=mock_used_stage_vars,
        )

        fake_stage.vars = vars
        fake_stage.save(update_fields=["_vars"])
        publish_validator = PublishValidator(fake_gateway, fake_stage, fake_resource_version)

        if will_error:
            with pytest.raises(Exception):
                publish_validator._validate_stage_vars(fake_stage, fake_resource_version.id)
            return

        assert publish_validator._validate_stage_vars(fake_stage, fake_resource_version.id) is None

    def test_validate_stage_plugins(
        self,
        fake_stage,
        fake_gateway,
        fake_resource_version,
        echo_plugin_type,
        echo_plugin_stage_binding,
        faker,
    ):
        echo_plugin2 = G(
            PluginConfig,
            gateway=fake_gateway,
            name="echo-plugin",
            type=echo_plugin_type,
            yaml=json.dumps(
                {
                    faker.random_element(["before_body", "body", "after_body"]): faker.pystr(),
                }
            ),
        )
        echo_plugin_stage_binding2 = G(
            PluginBinding,
            gateway=echo_plugin2.gateway,
            config=echo_plugin2,
            scope_type=PluginBindingScopeEnum.STAGE.value,
            scope_id=fake_stage.pk,
        )
        publish_validator = PublishValidator(fake_gateway, fake_stage, fake_resource_version)
        with pytest.raises(ReleaseValidationError):
            publish_validator._validate_stage_plugins()
