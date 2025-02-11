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

from apigateway.apps.label.models import APILabel
from apigateway.biz.plugin.plugin_synchronizers import PluginConfigData
from apigateway.biz.resource.importer.validate import ResourceImportValidator
from apigateway.core.models import Resource
from apigateway.utils.yaml import yaml_dumps


class TestResourceImportValidator:
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

        G(Resource, gateway=fake_gateway, name="getFoo")
        resource_data_list2 = [
            fake_resource_data.copy(update={"name": "get_foo"}, deep=True),
        ]
        validator2 = ResourceImportValidator(fake_gateway, resource_data_list2, False)
        validator2._validate_name()
        assert len(validator2.schema_validate_result) == 1

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
