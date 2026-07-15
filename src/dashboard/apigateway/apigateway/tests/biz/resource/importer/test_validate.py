# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from apigateway.apps.label.models import APILabel
from apigateway.apps.plugin.constants import PluginTypeCodeEnum, PluginTypeScopeEnum
from apigateway.apps.plugin.models import PluginType
from apigateway.biz.openapi import ResourceImportValidator
from apigateway.biz.plugin import PluginConfigData
from apigateway.biz.resource import ResourceAuthConfig, ResourceBackendConfig, ResourceData
from apigateway.core.constants import BackendKindEnum, GatewayKindEnum, ResourceKindEnum
from apigateway.core.models import Backend, Resource
from apigateway.utils.yaml import yaml_dumps

AI_ONLY_PLUGIN_CODES = (
    "ai-rate-limiting",
    "ai-prompt-guard",
    "ai-prompt-decorator",
)


def _plugin_yaml(plugin_type_code):
    if plugin_type_code == PluginTypeCodeEnum.AI_RATE_LIMITING.value:
        return yaml_dumps({"limit_strategy": "total_tokens", "rejected_code": 429})
    return yaml_dumps({"enabled": True})


class TestResourceImportValidator:
    def test_validate_ai_resource_kind_contract(self, fake_gateway):
        backend = G(Backend, gateway=fake_gateway, kind=BackendKindEnum.STANDARD.value)
        existing = G(Resource, gateway=fake_gateway, kind=ResourceKindEnum.STANDARD.value)
        resource_data = ResourceData(
            resource=existing,
            kind=ResourceKindEnum.AI.value,
            name="chat",
            method="POST",
            path="/chat",
            auth_config=ResourceAuthConfig(),
            backend=backend,
            backend_config=None,
        )

        errors = ResourceImportValidator(fake_gateway, [resource_data]).validate()

        messages = [error.message for error in errors]
        assert "普通网关不支持模型代理资源" in messages
        assert "资源 kind 创建后不能修改" in messages
        assert "资源 kind 与后端服务 kind 不一致" in messages

    def test_validate_ai_resource_accepts_ai_gateway_and_backend(self, fake_gateway):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()
        backend = G(Backend, gateway=fake_gateway, kind=BackendKindEnum.AI.value)
        resource_data = ResourceData(
            kind=ResourceKindEnum.AI.value,
            name="chat",
            method="POST",
            path="/chat",
            auth_config=ResourceAuthConfig(),
            backend=backend,
            backend_config=None,
        )

        errors = ResourceImportValidator(fake_gateway, [resource_data]).validate()

        assert not errors

    def test_validate_ai_resource_rejects_incompatible_plugin(
        self,
        fake_gateway,
        fake_plugin_type_bk_header_rewrite,
    ):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save(update_fields=["kind"])
        backend = G(Backend, gateway=fake_gateway, kind=BackendKindEnum.AI.value)
        resource_data = ResourceData(
            kind=ResourceKindEnum.AI.value,
            name="chat",
            method="POST",
            path="/chat",
            auth_config=ResourceAuthConfig(),
            backend=backend,
            backend_config=None,
            plugin_configs=[
                PluginConfigData(
                    type=fake_plugin_type_bk_header_rewrite.code,
                    yaml=yaml_dumps({"set": [{"key": "foo", "value": "bar"}], "remove": []}),
                )
            ],
        )

        errors = ResourceImportValidator(fake_gateway, [resource_data]).validate()

        assert any("bk-header-rewrite" in error.message and "不兼容" in error.message for error in errors)

    @pytest.mark.parametrize("plugin_type_code", AI_ONLY_PLUGIN_CODES)
    @pytest.mark.parametrize(
        ("resource_kind", "has_compatibility_error"),
        [(ResourceKindEnum.STANDARD.value, True), (ResourceKindEnum.AI.value, False)],
    )
    def test_validate_ai_only_plugin_by_resource_kind(
        self,
        fake_gateway,
        plugin_type_code,
        resource_kind,
        has_compatibility_error,
    ):
        if resource_kind == ResourceKindEnum.AI.value:
            fake_gateway.kind = GatewayKindEnum.AI.value
            fake_gateway.save(update_fields=["kind"])

        backend = G(Backend, gateway=fake_gateway, kind=resource_kind)
        G(
            PluginType,
            code=plugin_type_code,
            is_public=True,
            scope=PluginTypeScopeEnum.RESOURCE.value,
        )
        resource_data = ResourceData(
            kind=resource_kind,
            name="chat",
            method="POST",
            path="/chat",
            auth_config=ResourceAuthConfig(),
            backend=backend,
            backend_config=(
                ResourceBackendConfig(method="POST", path="/chat")
                if resource_kind == ResourceKindEnum.STANDARD.value
                else None
            ),
            plugin_configs=[
                PluginConfigData(
                    type=plugin_type_code,
                    yaml=_plugin_yaml(plugin_type_code),
                )
            ],
        )

        errors = ResourceImportValidator(fake_gateway, [resource_data]).validate()

        assert any(plugin_type_code in error.message and "不兼容" in error.message for error in errors) is (
            has_compatibility_error
        )

    def test_validate(self, fake_gateway, fake_resource_data):
        resource_data_list = [
            fake_resource_data.copy(deep=True),
        ]
        validator = ResourceImportValidator(fake_gateway, resource_data_list, True)
        validator.validate()

    def test_get_unchanged_resources(self, fake_gateway, fake_resource_data):
        resource_1 = G(Resource, gateway=fake_gateway)
        resource_2 = G(Resource, gateway=fake_gateway)

        resource_data_list = [
            fake_resource_data.copy(update={"resource": resource_1}, deep=True),
            fake_resource_data.copy(deep=True),
        ]

        validator = ResourceImportValidator(fake_gateway, resource_data_list, True)
        result = validator._get_unchanged_resources()
        assert result == []

        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        result = validator._get_unchanged_resources()
        assert len(result) == 1
        assert result[0]["id"] == resource_2.id

    def test_get_unspecified_resources(self, fake_gateway, fake_resource_data):
        resource_1 = G(Resource, gateway=fake_gateway)
        resource_2 = G(Resource, gateway=fake_gateway)

        resource_data_list = [
            fake_resource_data.copy(update={"resource": resource_1}, deep=True),
            fake_resource_data.copy(deep=True),
        ]

        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        result = validator.get_unspecified_resources()
        assert len(result) == 1
        assert result[0]["id"] == resource_2.id

    def test_get_label_names(self, fake_gateway, fake_resource_data):
        resource_data_list = [
            fake_resource_data.copy(update={"metadata": {"labels": ["foo"]}}, deep=True),
            fake_resource_data.copy(update={"metadata": {"labels": ["bar"]}}, deep=True),
        ]

        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        result = validator._get_label_names()

        assert len(result) == 2

    def test_validate_resources__error(self, fake_resource, fake_resource_data):
        resource_data_list = [
            fake_resource_data.copy(update={"resource": fake_resource}, deep=True),
            fake_resource_data.copy(update={"resource": fake_resource}, deep=True),
        ]

        validator = ResourceImportValidator(fake_resource.gateway, resource_data_list, True)
        validate_err_list = validator.validate()
        assert len(validate_err_list) == 2

    def test_validate_method_path__error(self, fake_resource, fake_resource_data):
        resource_data_list = [
            fake_resource_data.copy(update={"method": fake_resource.method, "path": fake_resource.path}, deep=True),
        ]
        validator = ResourceImportValidator(fake_resource.gateway, resource_data_list, False)
        validator._validate_method_path()
        assert len(validator.schema_validate_result) > 0

        resource_data_list = [
            fake_resource_data.copy(update={"method": "GET", "path": "/foo"}, deep=True),
            fake_resource_data.copy(update={"method": "GET", "path": "/foo"}, deep=True),
        ]
        validator = ResourceImportValidator(fake_resource.gateway, resource_data_list, True)

        validator._validate_method_path()
        assert len(validator.schema_validate_result) > 0

    def test_validate_method__error(self, fake_gateway, fake_resource_data):
        G(Resource, gateway=fake_gateway, method="GET", path="/foo")

        resource_data_list = [
            fake_resource_data.copy(update={"method": "ANY", "path": "/foo"}, deep=True),
        ]
        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        validator._validate_method()
        assert len(validator.schema_validate_result) > 0

    def test_validate_name__error(self, fake_gateway, fake_resource_data):
        G(Resource, gateway=fake_gateway, name="foo")
        resource_data_list = [
            fake_resource_data.copy(update={"name": "foo"}, deep=True),
        ]
        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        validator._validate_name()
        assert len(validator.schema_validate_result) > 0

        r2 = G(Resource, gateway=fake_gateway, name="getFoo")
        resource_data_list2 = [
            fake_resource_data.copy(update={"name": "get_foo"}, deep=True),
        ]
        validator2 = ResourceImportValidator(fake_gateway, resource_data_list2, False)
        validator2._validate_name()
        assert len(validator2.schema_validate_result) == 1

        # 更新
        G(Resource, gateway=fake_gateway, name="get_foo")
        resource_data_list3 = [
            fake_resource_data.copy(update={"resource": r2, "name": "getFoo"}, deep=True),
        ]
        validator3 = ResourceImportValidator(fake_gateway, resource_data_list3, False)
        validator3._validate_name()
        assert len(validator3.schema_validate_result) == 1

        # 导入资源同时存在 get_bar 和 getBar
        resource_data_list4 = [
            fake_resource_data.copy(update={"name": "get_bar"}, deep=True),
            fake_resource_data.copy(update={"name": "getBar"}, deep=True),
        ]
        validator4 = ResourceImportValidator(fake_gateway, resource_data_list4, False)
        validator4._validate_name()
        assert len(validator4.schema_validate_result) == 1

    def test_validate_match_subpath(self, fake_gateway, fake_resource_data):
        resource_data = fake_resource_data.copy(deep=True)
        resource_data.match_subpath = True
        resource_data.backend_config.match_subpath = False

        resource_data_list = [
            resource_data,
        ]

        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        validator._validate_match_subpath()
        assert len(validator.schema_validate_result) > 0

    def test_validate_resource_count__error(self, settings, fake_resource, fake_resource_data):
        settings.API_GATEWAY_RESOURCE_LIMITS = {
            "max_resource_count_per_gateway_whitelist": {"foo": 2},
            "max_resource_count_per_gateway": 1000,
        }
        resource_data_list = [
            fake_resource_data.copy(deep=True),
            fake_resource_data.copy(deep=True),
        ]
        fake_gateway = fake_resource.gateway
        fake_gateway.name = "foo"
        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        validator._validate_resource_count()
        assert len(validator.schema_validate_result) > 0

    @pytest.mark.parametrize(
        "resources, labels, expected",
        [
            (
                [{"labels": ["foo", "bar"]}],
                ["green", "blue"],
                ValueError,
            ),
            (
                [{"labels": ["foo", "bar"]}, {"labels": []}],
                [],
                ValueError,
            ),
            (
                [{"labels": ["foo"]}, {"labels": []}],
                ["foo"],
                None,
            ),
            (
                [{}, {"labels": []}],
                ["green", "blue"],
                None,
            ),
        ],
    )
    def test_validate_label_count(self, settings, fake_gateway, fake_resource_data, resources, labels, expected):
        settings.MAX_LABEL_COUNT_PER_GATEWAY = 1

        resource_data_list = [
            fake_resource_data.copy(update={"metadata": resource}, deep=True) for resource in resources
        ]
        for name in labels:
            G(APILabel, gateway=fake_gateway, name=name)

        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)

        validator._validate_label_count()

        if expected is None:
            assert len(validator.schema_validate_result) == 0
            return

        assert len(validator.schema_validate_result) > 0

    @pytest.mark.parametrize(
        "resources, labels, expected",
        [
            (
                [{"labels": ["foo", "bar"]}],
                ["Foo"],
                ValueError,
            ),
            (
                [{"labels": ["foo", "bar"]}],
                ["FOO", "BAR"],
                ValueError,
            ),
            (
                [{"labels": ["foo", "bar", "FOO", "Bar"]}],
                [],
                ValueError,
            ),
            (
                [{"labels": ["foo", "bar"]}, {"labels": ["FOO", "Bar"]}],
                [],
                ValueError,
            ),
            (
                [{"labels": ["foo"]}],
                ["foo"],
                None,
            ),
            (
                [{"labels": ["bar"]}],
                [],
                None,
            ),
            (
                [{"labels": []}],
                ["bar"],
                None,
            ),
        ],
    )
    def test_validate_label_name(self, fake_gateway, fake_resource_data, resources, labels, expected):
        resource_data_list = [
            fake_resource_data.copy(update={"metadata": resource}, deep=True) for resource in resources
        ]
        for name in labels:
            G(APILabel, gateway=fake_gateway, name=name)

        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)

        validator._validate_label_name()

        if expected is None:
            assert len(validator.schema_validate_result) == 0
            return

        assert len(validator.schema_validate_result) > 0

    @pytest.mark.parametrize(
        "plugin_configs, expected",
        [
            (
                {
                    "plugin_configs": None,
                },
                None,
            ),
            (
                {"plugin_configs": [PluginConfigData(type="echo", yaml="")]},
                None,
            ),
            (
                {
                    "plugin_configs": [
                        PluginConfigData(type="echo", yaml=""),
                        PluginConfigData(type="echo", yaml=""),
                    ]
                },
                ValueError,
            ),
            (
                {"plugin_configs": [PluginConfigData(type="not-exist-code", yaml="")]},
                ValueError,
            ),
        ],
    )
    def test_validate_plugin_type(self, fake_gateway, fake_resource_data, echo_plugin_type, plugin_configs, expected):
        resource_data_list = [
            fake_resource_data.copy(update=plugin_configs, deep=True),
        ]
        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        validator._validate_plugin_type()
        if expected is None:
            assert len(validator.schema_validate_result) == 0
            return

        assert len(validator.schema_validate_result) > 0

    @pytest.mark.parametrize(
        "plugin_configs, expected",
        [
            (
                {
                    "plugin_configs": None,
                },
                None,
            ),
            (
                {
                    "plugin_configs": [
                        PluginConfigData(
                            type="bk-header-rewrite",
                            yaml=yaml_dumps({"set": [{"key": "foo", "value": "bar"}], "remove": []}),
                        )
                    ]
                },
                None,
            ),
            (
                {"plugin_configs": [PluginConfigData(type="bk-header-rewrite", yaml=yaml_dumps({}))]},
                ValueError,
            ),
        ],
    )
    def test_validate_plugin_config(
        self, fake_gateway, fake_resource_data, fake_plugin_type_bk_header_rewrite, plugin_configs, expected
    ):
        resource_data_list = [
            fake_resource_data.copy(update=plugin_configs, deep=True),
        ]
        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        validator._validate_plugin_config()
        if expected is None:
            assert len(validator.schema_validate_result) == 0
            return

        assert len(validator.schema_validate_result) > 0

    @pytest.mark.parametrize(
        "resource_updates, expected_error_count",
        [
            # 正常情况：所有字段长度在限制内
            (
                {"name": "normal_name", "description": "normal description", "path": "/normal/path"},
                0,
            ),
            # name 超长 (限制 256)
            (
                {"name": "a" * 300},
                1,
            ),
            # description 超长 (限制 2048)
            (
                {"description": "a" * 2100},
                1,
            ),
            # description_en 超长 (限制 2048)
            (
                {"description_en": "a" * 2100},
                1,
            ),
            # path 超长 (限制 2048)
            (
                {"path": "/" + "a" * 2100},
                1,
            ),
            # 多个字段同时超长
            (
                {"name": "a" * 300, "description": "a" * 2100},
                2,
            ),
            # 边界情况：刚好在限制内
            (
                {"name": "a" * 256, "description": "a" * 2048},
                0,
            ),
            # 边界情况：刚好超出限制
            (
                {"name": "a" * 257, "description": "a" * 2049},
                2,
            ),
            # 空值不校验
            (
                {"description": "", "description_en": None},
                0,
            ),
        ],
    )
    def test_validate_resource_field_length(
        self, fake_gateway, fake_resource_data, resource_updates, expected_error_count
    ):
        resource_data_list = [
            fake_resource_data.copy(update=resource_updates, deep=True),
        ]
        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        validator._validate_resource_field_length()
        assert len(validator.schema_validate_result) == expected_error_count
