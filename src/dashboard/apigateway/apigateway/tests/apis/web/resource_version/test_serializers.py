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

import arrow
from django_dynamic_fixture import G

from apigateway.apis.web.resource_version import serializers
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.biz.backend import BackendHandler
from apigateway.biz.plugin_binding import PluginBindingHandler
from apigateway.core.models import Gateway, ResourceVersion


class TestResourceVersionInfoSLZ:
    def test_create(self, fake_gateway, fake_resource):
        slz = serializers.ResourceVersionCreateInputSLZ(
            data={
                "version": "1.0.2",
                "comment": "",
            },
            context={
                "gateway": fake_gateway,
            },
        )
        slz.is_valid()
        assert not slz.errors


class TestResourceVersionListOutputSLZ:
    def test_to_representation(self):
        gateway = G(Gateway)
        resource_version = G(
            ResourceVersion,
            gateway=gateway,
            version="1.0.1",
            created_time=arrow.get("2019-01-01 12:30:00").datetime,
            created_by="x"
        )

        queryset = ResourceVersion.objects.filter(gateway=gateway).values(
            "id", "version", "schema_version", "comment", "created_time", "created_by"
        )

        slz = serializers.ResourceVersionListOutputSLZ(
            instance=queryset,
            many=True,
            context={
                "released_stages": {
                    resource_version.id: [
                        {
                            "id": 1,
                            "name": "prod",
                        },
                        {
                            "id": 2,
                            "name": "test",
                        },
                    ]
                },
                "resource_version_ids_sdk_count": {},
            },
        )
        assert slz.data == [
            {
                "id": resource_version.id,
                "version": resource_version.version,
                "schema_version": resource_version.schema_version,
                "comment": resource_version.comment,
                "sdk_count": 0,
                "released_stages": [
                    {
                        "id": 1,
                        "name": "prod",
                    },
                    {
                        "id": 2,
                        "name": "test",
                    },
                ],
                "created_by": "x",
                "created_time": "2019-01-01 20:30:00",
            },
        ]


class TestResourceVersionRetrieveOutputSLZ:
    def test_to_representation_v1(
        self, fake_backend, fake_stage, fake_gateway, fake_resource_version_v1, echo_plugin_stage_binding
    ):
        slz = serializers.ResourceVersionRetrieveOutputSLZ(
            instance=fake_resource_version_v1,
            context={
                "resource_backends": BackendHandler.get_id_to_instance(fake_gateway.id),
                "resource_backend_configs": BackendHandler.get_backend_configs_by_stage(
                    fake_gateway.id, fake_stage.id
                ),
                "is_schema_v2": fake_resource_version_v1.is_schema_v2,
                "stage_plugins": {},
                "resource_doc_updated_time": {},
            },
        )
        expected_data = {
            "id": fake_resource_version_v1.id,
            "version": fake_resource_version_v1.version,
            "comment": fake_resource_version_v1.comment,
            "schema_version": fake_resource_version_v1.schema_version,
            "resources": [
                {
                    "name": fake_resource_version_v1.data[0]["name"],
                    "method": fake_resource_version_v1.data[0]["method"],
                    "path": fake_resource_version_v1.data[0]["path"],
                    "description": fake_resource_version_v1.data[0]["description"],
                    "description_en": fake_resource_version_v1.data[0]["description_en"],
                    "gateway_label_ids": fake_resource_version_v1.data[0]["api_labels"],
                    "match_subpath": fake_resource_version_v1.data[0]["match_subpath"],
                    "is_public": fake_resource_version_v1.data[0]["is_public"],
                    "allow_apply_permission": fake_resource_version_v1.data[0]["allow_apply_permission"],
                    "doc_updated_time": "",
                    "proxy": {
                        "config": fake_resource_version_v1.data[0]["proxy"]["config"],
                        "backend": {
                            "id": fake_backend.id,
                            "name": fake_backend.name,
                            "config": {
                                "type": "node",
                                "timeout": 30,
                                "loadbalance": "roundrobin",
                                "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 100}],
                            },
                        },
                    },
                    "contexts": fake_resource_version_v1.data[0]["contexts"],
                    "plugins": [],
                }
            ],
            "created_time": fake_resource_version_v1.created_time,
            "created_by": fake_resource_version_v1.created_by,
        }
        assert slz.data == expected_data

    def test_to_representation_v2(
        self, fake_backend, fake_stage, fake_gateway, fake_resource_version_v2, echo_plugin_stage_binding
    ):
        stage_plugin_bindings = PluginBindingHandler.get_stage_plugin_bindings(fake_gateway.id, fake_stage.id)
        stage_plugins = {}
        for plugin_type, plugin_binding in stage_plugin_bindings.items():
            plugin_config = plugin_binding.snapshot()
            plugin_config["binding_type"] = PluginBindingScopeEnum.STAGE.value
            stage_plugins[plugin_type] = plugin_config
        slz = serializers.ResourceVersionRetrieveOutputSLZ(
            instance=fake_resource_version_v2,
            context={
                "resource_backends": BackendHandler.get_id_to_instance(fake_gateway.id),
                "resource_backend_configs": BackendHandler.get_backend_configs_by_stage(
                    fake_gateway.id, fake_stage.id
                ),
                "is_schema_v2": fake_resource_version_v2.is_schema_v2,
                "stage_plugins": stage_plugins,
                "resource_doc_updated_time": {},
            },
        )
        expected_data = {
            "id": fake_resource_version_v2.id,
            "version": fake_resource_version_v2.version,
            "comment": fake_resource_version_v2.comment,
            "schema_version": fake_resource_version_v2.schema_version,
            "resources": [
                {
                    "name": fake_resource_version_v2.data[0]["name"],
                    "method": fake_resource_version_v2.data[0]["method"],
                    "path": fake_resource_version_v2.data[0]["path"],
                    "description": fake_resource_version_v2.data[0]["description"],
                    "description_en": fake_resource_version_v2.data[0]["description_en"],
                    "gateway_label_ids": fake_resource_version_v2.data[0]["api_labels"],
                    "match_subpath": fake_resource_version_v2.data[0]["match_subpath"],
                    "is_public": fake_resource_version_v2.data[0]["is_public"],
                    "allow_apply_permission": fake_resource_version_v2.data[0]["allow_apply_permission"],
                    "doc_updated_time": "",
                    "proxy": {
                        "config": fake_resource_version_v2.data[0]["proxy"]["config"],
                        "backend": {
                            "id": fake_backend.id,
                            "name": fake_backend.name,
                            "config": {
                                "type": "node",
                                "timeout": 30,
                                "loadbalance": "roundrobin",
                                "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 100}],
                            },
                        },
                    },
                    "contexts": fake_resource_version_v2.data[0]["contexts"],
                    "plugins": [
                        {
                            "id": echo_plugin_stage_binding.id,
                            "type": echo_plugin_stage_binding.get_type(),
                            "name": echo_plugin_stage_binding.config.type.name,
                            "config": echo_plugin_stage_binding.get_config(),
                            "binding_type": "stage",
                        },
                    ],
                }
            ],
            "created_time": fake_resource_version_v2.created_time,
            "created_by": fake_resource_version_v2.created_by,
        }
        assert slz.data == expected_data
