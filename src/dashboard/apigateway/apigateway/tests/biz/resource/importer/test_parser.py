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

from apigateway.biz.resource.importer.parser import ResourceDataConvertor
from apigateway.core.models import Backend, Resource


class TestResourceDataConvertor:
    def test_convert(self, fake_gateway, faker):
        resource_1 = G(Resource, gateway=fake_gateway, name="test1", method="GET", path="/test1")
        resource_2 = G(Resource, gateway=fake_gateway, name="test2", method="POST", path="/test2")

        backend_1 = G(Backend, gateway=fake_gateway, name="foo")
        backend_2 = G(Backend, gateway=fake_gateway, name="default")

        resources = [
            {
                "id": resource_1.id,
                "name": "test1",
                "method": "GET",
                "path": "/test1",
                "backend_name": "foo",
                "backend_config": {
                    "method": "GET",
                    "path": "/backend/test1",
                },
            },
            {
                "name": "test2_1",
                "method": "POST",
                "path": "/test2",
                "backend_config": {
                    "method": "POST",
                    "path": "/backend/test2",
                },
            },
        ]
        convertor = ResourceDataConvertor(fake_gateway, resources)
        result = convertor.convert()

        assert result[0].resource == resource_1
        assert result[0].backend == backend_1
        assert result[0].backend_config.path == "/backend/test1"

        assert result[1].resource == resource_2
        assert result[1].backend == backend_2
        assert result[1].backend_config.path == "/backend/test2"

    def test_convert__error(self, fake_resource):
        resources = [
            {
                "id": fake_resource.id,
                "name": "test1",
                "method": "GET",
                "path": "/test1",
                "backend_name": "not_exist",
                "backend_config": {
                    "method": "GET",
                    "path": "/backend/test1",
                },
            },
        ]

        convertor = ResourceDataConvertor(fake_resource.gateway, resources)
        with pytest.raises(ValueError):
            convertor.convert()

    def test_get_resource_obj(self, fake_resource):
        resource_id_to_obj = {fake_resource.id: fake_resource}
        resource_key_to_resource_obj = {f"{fake_resource.method}:{fake_resource.path}": fake_resource}

        convertor = ResourceDataConvertor(fake_resource.gateway, [])

        resource_obj = convertor._get_resource_obj(
            {"id": fake_resource.id}, resource_id_to_obj, resource_key_to_resource_obj
        )
        assert resource_obj == fake_resource

        resource_obj = convertor._get_resource_obj(
            {"method": fake_resource.method, "path": fake_resource.path},
            resource_id_to_obj,
            resource_key_to_resource_obj,
        )
        assert resource_obj == fake_resource

        with pytest.raises(ValueError):
            convertor._get_resource_obj({"id": 0}, resource_id_to_obj, resource_key_to_resource_obj)
