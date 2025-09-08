#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig
from apigateway.biz.validators import (
    BKAppCodeListValidator,
    BKAppCodeValidator,
    MaxCountPerGatewayValidator,
    PublishValidator,
    ReleaseValidationError,
    ResourceIDValidator,
    ResourceVersionValidator,
    SchemeHostInputValidator,
    StageVarsValidator,
    UpstreamValidator,
)
from apigateway.common.constants import CallSourceTypeEnum
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.constants import BackendTypeEnum, GatewayStatusEnum
from apigateway.core.models import Backend, BackendConfig, Gateway, Release, Resource, ResourceVersion, Stage
from apigateway.tests.utils.testing import create_request

pytestmark = pytest.mark.django_db


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
        # G(
        #     Proxy,
        #     type=ProxyTypeEnum.HTTP.value,
        #     resource=fake_resource,
        #     backend=backend2,
        #     _config=json.dumps(
        #         {
        #             "method": faker.http_method(),
        #             "path": faker.uri_path(),
        #             "match_subpath": False,
        #             "timeout": faker.random_int(),
        #         }
        #     ),
        #     schema=SchemaFactory().get_proxy_schema(ProxyTypeEnum.HTTP.value),
        # )
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

    def test_validate_stage_backends(self, fake_stage, fake_gateway):
        backend = G(
            Backend,
            gateway=fake_gateway,
            type="http",
            name="default",
            description="test",
        )

        stage2 = G(
            Stage,
            gateway=fake_gateway,
            name="test_stage2",
            description="test",
        )

        G(
            BackendConfig,
            gateway=fake_gateway,
            backend=backend,
            stage=fake_stage,
            config={
                "timeout": 30,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "ee.com", "weight": 100}],
            },
        )

        G(
            BackendConfig,
            gateway=fake_gateway,
            backend=backend,
            stage=stage2,
            config={
                "timeout": 30,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "", "host": "", "weight": 100}],
            },
        )

        resource_version = G(
            ResourceVersion,
            gateway=fake_gateway,
            version="1",
            _data=json.dumps(
                [
                    {
                        "id": 1,
                        "name": "approval_add_workitems",
                        "proxy": {
                            "id": 28,
                            "type": "http",
                            "backend_id": backend.id,
                            "config": json.dumps(
                                {"method": "ANY", "path": "/api/v2/", "match_subpath": False, "timeout": 0}
                            ),
                        },
                    }
                ]
            ),
        )

        publish_validator = PublishValidator(fake_gateway, fake_stage, resource_version)
        publish_validator._validate_stage_backends()

    def test_validate_stage_backends_without_default_backend(
        self, fake_stage, fake_backend, fake_default_empty_backend, fake_resource, fake_gateway
    ):
        """
        测试编辑区资源没有绑定default backend（host为空）的情况
        """
        publish_validator = PublishValidator(fake_gateway, fake_stage, None)
        with pytest.raises(Exception):
            publish_validator._validate_stage_backends()


class TestSchemeHostInputValidator:
    @pytest.mark.parametrize(
        "data, expected, will_error",
        [
            (
                {
                    "backend_type": BackendTypeEnum.HTTP.value,
                    "hosts": [{"scheme": "http"}],
                    "source": CallSourceTypeEnum.Web.value,
                },
                None,
                False,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.HTTP.value,
                    "hosts": [{"scheme": "https"}],
                    "source": CallSourceTypeEnum.Web.value,
                },
                None,
                False,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.HTTP.value,
                    "hosts": [{"scheme": "http"}, {"scheme": "http"}],
                    "source": CallSourceTypeEnum.Web.value,
                },
                None,
                False,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.HTTP.value,
                    "hosts": [{"scheme": "https"}, {"scheme": "https"}],
                    "source": CallSourceTypeEnum.Web.value,
                },
                None,
                False,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.HTTP.value,
                    "hosts": [{"scheme": "http"}, {"scheme": "https"}],
                    "source": CallSourceTypeEnum.Web.value,
                },
                {
                    "error_message": "[ErrorDetail(string='后端服务【Test Backend】的配置 scheme 同时存在 http 和 https， 需要保持一致。', code='invalid')]",
                },
                True,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.GRPC.value,
                    "hosts": [{"scheme": "grpc"}],
                    "source": CallSourceTypeEnum.Web.value,
                },
                None,
                False,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.GRPC.value,
                    "hosts": [{"scheme": "grpcs"}],
                    "source": CallSourceTypeEnum.Web.value,
                },
                None,
                False,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.GRPC.value,
                    "hosts": [{"scheme": "grpc"}, {"scheme": "grpc"}],
                    "source": CallSourceTypeEnum.Web.value,
                },
                None,
                False,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.GRPC.value,
                    "hosts": [{"scheme": "grpcs"}, {"scheme": "grpcs"}],
                    "source": CallSourceTypeEnum.Web.value,
                },
                None,
                False,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.GRPC.value,
                    "hosts": [{"scheme": "grpc"}, {"scheme": "grpcs"}],
                    "source": CallSourceTypeEnum.Web.value,
                },
                {
                    "error_message": "[ErrorDetail(string='后端服务【Test Backend】的配置 scheme 同时存在 grpc 和 grpcs， 需要保持一致。', code='invalid')]",
                },
                True,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.HTTP.value,
                    "hosts": [{"host": "http://example.com"}],
                    "source": CallSourceTypeEnum.OpenAPI.value,
                },
                None,
                False,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.HTTP.value,
                    "hosts": [{"host": "http://localhost"}],
                    "source": CallSourceTypeEnum.OpenAPI.value,
                },
                {
                    "error_message": "[ErrorDetail(string='后端服务【Test Backend】的配置，host: localhost 不能使用该地址。', code='invalid')]",
                },
                True,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.HTTP.value,
                    "hosts": [{"host": "http://127.0.0.1"}],
                    "source": CallSourceTypeEnum.OpenAPI.value,
                },
                {
                    "error_message": "[ErrorDetail(string='后端服务【Test Backend】的配置，host: 127.0.0.1 不能使用该地址。', code='invalid')]",
                },
                True,
            ),
            (
                {
                    "backend_type": BackendTypeEnum.HTTP.value,
                    "hosts": [{"host": "http://0.0.0.0"}],
                    "source": CallSourceTypeEnum.OpenAPI.value,
                },
                {
                    "error_message": "[ErrorDetail(string='后端服务【Test Backend】的配置，host: 0.0.0.0 不能使用该地址。', code='invalid')]",
                },
                True,
            ),
        ],
    )
    def test_validate_scheme(self, fake_backend, fake_grpc_backend, data, expected, will_error):
        if data["backend_type"] == BackendTypeEnum.HTTP.value:
            backend_name = fake_backend.name
            validator = SchemeHostInputValidator(fake_backend, data["hosts"])
        else:
            backend_name = fake_grpc_backend.name
            validator = SchemeHostInputValidator(fake_grpc_backend, data["hosts"])
        # 捕获可能的异常
        # 假设这个方法在某些条件下会抛出异常
        if will_error:
            # 验证异常消息是否符合预期
            with pytest.raises(Exception) as exc_info:
                validator.validate_scheme(data["source"])
            expected_msg = expected["error_message"].replace("Test Backend", backend_name)
            assert str(exc_info.value) == expected_msg


class TestStageVarsValidator:
    class StageSLZ(serializers.ModelSerializer):
        gateway = serializers.HiddenField(default=CurrentGatewayDefault())
        vars = serializers.DictField(label="环境变量", child=serializers.CharField())

        class Meta:
            model = Stage
            fields = (
                "gateway",
                "vars",
            )

            validators = [StageVarsValidator()]

    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.gateway = G(Gateway)
        self.request = create_request()
        self.request.gateway = self.gateway

    def test_validate_vars_keys(self):
        data = [
            {
                "params": {
                    # error, first is not char
                    "vars": {
                        "12345": "a",
                    },
                },
                "will_error": True,
            },
            {
                "params": {
                    # error, over length
                    "vars": {
                        "a" * 51: "a",
                    },
                },
                "will_error": True,
            },
            {
                "params": {
                    # error, include -
                    "vars": {
                        "abc-d": "a",
                    },
                },
                "will_error": True,
            },
            {
                "params": {
                    "vars": {
                        "domian_2": "a",
                    },
                },
                "will_error": False,
            },
            {
                "params": {
                    "vars": {
                        "a" * 50: "a",
                    },
                },
                "will_error": False,
            },
        ]
        for test in data:
            slz = self.StageSLZ(data=test["params"], context={"request": self.request})
            slz.is_valid()
            if test.get("will_error"):
                assert slz.errors, test["params"]
            else:
                assert not slz.errors, test["params"]

    def test_validate_vars_values(self, mocker):
        stage = G(Stage, gateway=self.gateway, status=1)
        resource_version = G(ResourceVersion, gateway=self.gateway)
        G(Release, gateway=self.gateway, stage=stage, resource_version=resource_version)

        data = [
            # ok
            {
                "vars": {
                    "prefix": "/o",
                    "domain": "bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "will_error": False,
            },
            # allow_var_not_exist=True
            {
                "vars": {
                    "domain": "bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "allow_var_not_exist": True,
                "will_error": False,
            },
            {
                "vars": {
                    "prefix": "/test/",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "allow_var_not_exist": True,
                "will_error": False,
            },
            # var in path not exist
            {
                "vars": {
                    "domain": "bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "will_error": True,
            },
            # var in path invalid
            {
                "vars": {
                    "prefix": "/test/?a=b",
                    "domain": "bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "will_error": True,
            },
            {
                "vars": {
                    "prefix": "/test/?a=b",
                    "domain": "bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "allow_var_not_exist": True,
                "will_error": True,
            },
            # var in hosts not exist
            {
                "vars": {
                    "prefix": "/test/",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "will_error": True,
            },
            # var in hosts invalid
            {
                "vars": {
                    "prefix": "/test/",
                    "domain": "http://bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "will_error": True,
            },
            {
                "vars": {
                    "prefix": "/test/",
                    "domain": "http://bking.com",
                },
                "mock_used_stage_vars": {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                "allow_var_not_exist": True,
                "will_error": True,
            },
        ]
        for test in data:
            slz = self.StageSLZ(
                instance=stage,
                data={
                    "vars": test["vars"],
                },
                context={
                    "request": self.request,
                    "allow_var_not_exist": test.get("allow_var_not_exist", False),
                },
            )
            mocker.patch(
                "apigateway.biz.validators.ResourceVersionHandler.get_used_stage_vars",
                return_value=test["mock_used_stage_vars"],
            )

            slz.is_valid()
            if test.get("will_error"):
                assert slz.errors
            else:
                assert not slz.errors


class TestUpstreamValidator:
    """测试上游配置校验器"""

    def test_validate_wrr_loadbalance_with_weight(self):
        """测试 WRR 负载均衡类型，所有 host 都有权重"""
        validator = UpstreamValidator()
        attrs = {
            "loadbalance": "weighted-roundrobin",
            "hosts": [
                {"host": "example1.com", "weight": 100},
                {"host": "example2.com", "weight": 200},
            ],
        }
        serializer = None

        # 应该通过验证
        result = validator(attrs, serializer)
        assert result is None

    def test_validate_wrr_loadbalance_without_weight(self):
        """测试 WRR 负载均衡类型，有 host 没有权重"""
        validator = UpstreamValidator()
        attrs = {
            "loadbalance": "weighted-roundrobin",
            "hosts": [
                {"host": "example1.com", "weight": 100},
                {"host": "example2.com"},  # 没有权重
            ],
        }
        serializer = None

        # 应该抛出验证错误
        with pytest.raises(serializers.ValidationError) as exc_info:
            validator(attrs, serializer)
        assert "负载均衡类型为 Weighted-RR 时，Host 权重必填" in str(exc_info.value)

    def test_validate_chash_loadbalance_without_hash_on(self):
        """测试 CHash 负载均衡类型，缺少 hash_on 参数"""
        validator = UpstreamValidator()
        attrs = {"loadbalance": "chash", "key": "some_key", "hosts": [{"host": "example.com"}]}
        serializer = None

        # 应该抛出验证错误
        with pytest.raises(serializers.ValidationError) as exc_info:
            validator(attrs, serializer)
        assert "hash_on is required when loadbalance is chash" in str(exc_info.value)

    def test_validate_chash_loadbalance_without_key(self):
        """测试 CHash 负载均衡类型，缺少 key 参数"""
        validator = UpstreamValidator()
        attrs = {"loadbalance": "chash", "hash_on": "vars", "hosts": [{"host": "example.com"}]}
        serializer = None

        # 应该抛出验证错误
        with pytest.raises(serializers.ValidationError) as exc_info:
            validator(attrs, serializer)
        assert "key is required when loadbalance is chash" in str(exc_info.value)

    def test_validate_chash_vars_hash_on_without_dollar_prefix(self):
        """测试 CHash 负载均衡类型，vars hash_on 但 key 不以 $ 开头"""
        validator = UpstreamValidator()
        attrs = {
            "loadbalance": "chash",
            "hash_on": "vars",
            "key": "invalid_key",  # 不以 $ 开头
            "hosts": [{"host": "example.com"}],
        }
        serializer = None

        # 应该抛出验证错误
        with pytest.raises(serializers.ValidationError) as exc_info:
            validator(attrs, serializer)
        assert "key must start with $ when hash_on is vars" in str(exc_info.value)

    def test_validate_chash_vars_hash_on_with_dollar_prefix(self):
        """测试 CHash 负载均衡类型，vars hash_on 且 key 以 $ 开头"""
        validator = UpstreamValidator()
        attrs = {
            "loadbalance": "chash",
            "hash_on": "vars",
            "key": "$valid_key",  # 以 $ 开头
            "hosts": [{"host": "example.com"}],
        }
        serializer = None

        # 应该通过验证
        result = validator(attrs, serializer)
        assert result is None

    def test_validate_chash_vars_combinations_hash_on_without_dollar_prefix(self):
        """测试 CHash 负载均衡类型，vars_combinations hash_on 但 key 不以 $ 开头"""
        validator = UpstreamValidator()
        attrs = {
            "loadbalance": "chash",
            "hash_on": "vars_combinations",
            "key": "invalid_key",  # 不以 $ 开头
            "hosts": [{"host": "example.com"}],
        }
        serializer = None

        # 应该抛出验证错误
        with pytest.raises(serializers.ValidationError) as exc_info:
            validator(attrs, serializer)
        assert "key must start with $ when hash_on is vars" in str(exc_info.value)

    def test_validate_chash_vars_combinations_hash_on_with_dollar_prefix(self):
        """测试 CHash 负载均衡类型，vars_combinations hash_on 且 key 以 $ 开头"""
        validator = UpstreamValidator()
        attrs = {
            "loadbalance": "chash",
            "hash_on": "vars_combinations",
            "key": "$valid_key",  # 以 $ 开头
            "hosts": [{"host": "example.com"}],
        }
        serializer = None

        # 应该通过验证
        result = validator(attrs, serializer)
        assert result is None

    def test_validate_chash_header_hash_on_without_http_prefix(self):
        """测试 CHash 负载均衡类型，header hash_on 但 key 不以 http_ 开头"""
        validator = UpstreamValidator()
        attrs = {
            "loadbalance": "chash",
            "hash_on": "header",
            "key": "invalid_key",  # 不以 http_ 开头
            "hosts": [{"host": "example.com"}],
        }
        serializer = None

        # 应该抛出验证错误
        with pytest.raises(serializers.ValidationError) as exc_info:
            validator(attrs, serializer)
        assert "key must start with http_ when hash_on is header" in str(exc_info.value)

    def test_validate_chash_header_hash_on_with_http_prefix(self):
        """测试 CHash 负载均衡类型，header hash_on 且 key 以 http_ 开头"""
        validator = UpstreamValidator()
        attrs = {
            "loadbalance": "chash",
            "hash_on": "header",
            "key": "http_user_agent",  # 以 http_ 开头
            "hosts": [{"host": "example.com"}],
        }
        serializer = None

        # 应该通过验证
        result = validator(attrs, serializer)
        assert result is None

    def test_validate_chash_cookie_hash_on_without_cookie_prefix(self):
        """测试 CHash 负载均衡类型，cookie hash_on 但 key 不以 cookie_ 开头"""
        validator = UpstreamValidator()
        attrs = {
            "loadbalance": "chash",
            "hash_on": "cookie",
            "key": "invalid_key",  # 不以 cookie_ 开头
            "hosts": [{"host": "example.com"}],
        }
        serializer = None

        # 应该抛出验证错误
        with pytest.raises(serializers.ValidationError) as exc_info:
            validator(attrs, serializer)
        assert "key must start with cookie_ when hash_on is cookie" in str(exc_info.value)

    def test_validate_chash_cookie_hash_on_with_cookie_prefix(self):
        """测试 CHash 负载均衡类型，cookie hash_on 且 key 以 cookie_ 开头"""
        validator = UpstreamValidator()
        attrs = {
            "loadbalance": "chash",
            "hash_on": "cookie",
            "key": "cookie_session_id",  # 以 cookie_ 开头
            "hosts": [{"host": "example.com"}],
        }
        serializer = None

        # 应该通过验证
        result = validator(attrs, serializer)
        assert result is None

    def test_validate_other_loadbalance_types(self):
        """测试其他负载均衡类型（RR, EWMA, LEAST_CONN）"""
        validator = UpstreamValidator()
        other_loadbalance_types = ["roundrobin", "ewma", "least_conn"]

        for loadbalance_type in other_loadbalance_types:
            attrs = {"loadbalance": loadbalance_type, "hosts": [{"host": "example.com"}]}
            serializer = None

            # 应该通过验证
            result = validator(attrs, serializer)
            assert result is None
