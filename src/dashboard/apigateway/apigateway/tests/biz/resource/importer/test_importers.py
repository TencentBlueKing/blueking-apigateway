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
from apigateway.apps.plugin.constants import PluginBindingSourceEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig
from apigateway.biz.plugin.plugin_synchronizers import PluginConfigData
from apigateway.biz.resource.importer import ResourceDataConvertor, ResourcesImporter
from apigateway.core.models import Backend, Resource
from apigateway.utils.yaml import yaml_dumps


class TestResourcesImporter:
    def test_from_resources(self, fake_gateway):
        G(Backend, gateway=fake_gateway, name="foo")
        resources = [
            {
                "name": "test",
                "method": "GET",
                "path": "/test",
                "backend_name": "foo",
                "backend_config": {
                    "method": "GET",
                    "path": "/backend/test",
                },
            }
        ]

        resource_data_list = ResourceDataConvertor(fake_gateway, resources).convert()
        importer = ResourcesImporter.from_resources(fake_gateway, resource_data_list)
        assert len(importer.resource_data_list) == 1

    def test_import_resources(self, fake_gateway, fake_resource_data):
        resource_1 = G(Resource, gateway=fake_gateway, name="test1", method="GET", path="/test1")
        resource_2 = G(Resource, gateway=fake_gateway, name="test2", method="POST", path="/test2")
        resource_2_id = resource_2.id

        G(Backend, gateway=fake_gateway, name="default")

        resource_data_list = [
            fake_resource_data.copy(update={"resource": resource_1, "name": "foo1", "path": "/foo1"}, deep=True),
            fake_resource_data.copy(update={"name": "foo2", "path": "/foo2"}, deep=True),
        ]
        importer = ResourcesImporter(
            fake_gateway,
            resource_data_list,
            need_delete_unspecified_resources=True,
        )
        importer.import_resources()

        resource_ids = list(Resource.objects.filter(gateway=fake_gateway).values_list("id", flat=True))
        assert len(resource_ids) == 2
        assert resource_2_id not in resource_ids
        assert resource_1.id in resource_ids

    @pytest.mark.parametrize(
        "selected_resources, expected",
        [
            (
                None,
                2,
            ),
            (
                [{"name": "test1"}],
                1,
            ),
            (
                [{"name": "test1"}, {"name": "test2"}],
                2,
            ),
            (
                [{"name": "test3"}, {"name": "test4"}],
                0,
            ),
        ],
    )
    def test_filter_selected_resource_data_list(self, fake_gateway, fake_resource_data, selected_resources, expected):
        resource_data_list = [
            fake_resource_data.copy(update={"name": "test1", "method": "GET"}, deep=True),
            fake_resource_data.copy(update={"name": "test2", "method": "POST"}, deep=True),
        ]
        importer = ResourcesImporter(fake_gateway, [], selected_resources=None)
        result = importer._filter_selected_resource_data_list(selected_resources, resource_data_list)
        assert len(result) == expected

    def test_delete_unspecified_resources(self, fake_gateway, fake_resource_data):
        resource_1 = G(Resource, gateway=fake_gateway, name="test1", method="GET", path="/test1")
        resource_2 = G(Resource, gateway=fake_gateway, name="test2", method="POST", path="/test2")
        resource_2_id = resource_2.id

        resource_data_list = [
            fake_resource_data.copy(update={"resource": resource_1}, deep=True),
        ]

        importer = ResourcesImporter(fake_gateway, resource_data_list, need_delete_unspecified_resources=True)
        result = importer._delete_unspecified_resources()
        assert len(result) == 1
        assert result[0]["id"] == resource_2_id
        assert not Resource.objects.filter(id=resource_2_id).exists()

    def test_create_not_exist_labels(self, fake_gateway, fake_resource_data):
        G(APILabel, gateway=fake_gateway, name="label1")

        resource_data_list = [
            fake_resource_data.copy(
                update={"metadata": {"labels": ["label1", "label2"]}, "name": "foo1", "method": "GET"}, deep=True
            ),
            fake_resource_data.copy(
                update={"metadata": {"labels": ["label1", "label3"]}, "name": "foo2", "method": "POST"}, deep=True
            ),
        ]

        importer = ResourcesImporter(fake_gateway, resource_data_list)
        importer._create_not_exist_labels()

        assert APILabel.objects.filter(gateway=fake_gateway).count() == 3

    def test_complete_label_ids(self, fake_gateway, fake_resource_data):
        label_1 = G(APILabel, gateway=fake_gateway, name="label1")
        label_2 = G(APILabel, gateway=fake_gateway, name="label2")

        resource_data_list = [
            fake_resource_data.copy(
                update={"metadata": {"labels": ["label1"]}, "name": "foo1", "method": "GET"}, deep=True
            ),
            fake_resource_data.copy(
                update={"metadata": {"labels": ["label2"]}, "name": "foo2", "method": "POST"}, deep=True
            ),
        ]

        importer = ResourcesImporter(fake_gateway, resource_data_list)
        importer._complete_label_ids()

        assert resource_data_list[0].label_ids == [label_1.id]
        assert resource_data_list[1].label_ids == [label_2.id]

    def test_sync_plugins(self, fake_gateway, fake_resource_data, fake_plugin_type_bk_header_rewrite):
        resource_1 = G(Resource, gateway=fake_gateway, method="GET")
        resource_2 = G(Resource, gateway=fake_gateway, method="POST")

        plugin_config_1 = G(PluginConfig, gateway=fake_gateway, type=fake_plugin_type_bk_header_rewrite)
        plugin_config_2 = G(PluginConfig, gateway=fake_gateway, type=fake_plugin_type_bk_header_rewrite)

        G(
            PluginBinding,
            gateway=fake_gateway,
            config=plugin_config_1,
            scope_type="resource",
            scope_id=resource_1.id,
        )
        G(
            PluginBinding,
            gateway=fake_gateway,
            config=plugin_config_2,
            scope_type="resource",
            scope_id=resource_2.id,
        )

        resource_3 = G(Resource, gateway=fake_gateway, method="PUT")
        plugin_config_3_yaml_import = G(PluginConfig, gateway=fake_gateway, type=fake_plugin_type_bk_header_rewrite)

        G(
            PluginBinding,
            gateway=fake_gateway,
            config=plugin_config_3_yaml_import,
            source=PluginBindingSourceEnum.YAML_IMPORT.value,
            scope_type="resource",
            scope_id=resource_3.id,
        )

        resource_data_list = [
            fake_resource_data.copy(
                update={"resource": resource_1, "plugin_configs": None, "name": "foo", "method": "GET"}, deep=True
            ),
            fake_resource_data.copy(
                update={
                    "resource": resource_2,
                    "plugin_configs": [
                        PluginConfigData(
                            type="bk-header-rewrite",
                            yaml=yaml_dumps({"set": [{"key": "foo", "value": "bar"}], "remove": []}),
                        )
                    ],
                    "name": "bar",
                    "method": "POST",
                },
                deep=True,
            ),
            fake_resource_data.copy(
                update={"resource": resource_3, "plugin_configs": None, "name": "foo2", "method": "PUT"}, deep=True
            ),
        ]

        importer = ResourcesImporter(fake_gateway, resource_data_list)
        importer._sync_plugins()

        assert PluginBinding.objects.filter(scope_type="resource", scope_id=resource_1.id).count() == 1
        assert PluginBinding.objects.get(scope_type="resource", scope_id=resource_2.id).config.config == {
            "set": [{"key": "foo", "value": "bar"}],
            "remove": [],
        }
        # 配置插件为空，删除之前import的插件配置
        assert PluginBinding.objects.filter(scope_type="resource", scope_id=resource_3.id).count() == 0
