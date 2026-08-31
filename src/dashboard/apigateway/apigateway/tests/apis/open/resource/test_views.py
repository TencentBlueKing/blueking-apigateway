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
import json

from ddf import G

from apigateway.apps.support.models import ResourceDoc
from apigateway.core.constants import BackendKindEnum, GatewayKindEnum, ResourceKindEnum
from apigateway.core.models import Backend, Proxy, Resource


class TestResourceSyncApi:
    def test_sync_ai_resource(self, request_view, fake_gateway, ignore_related_app_permission):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()
        backend = G(Backend, gateway=fake_gateway, name="openai-primary", kind=BackendKindEnum.AI.value)
        content = json.dumps(
            {
                "swagger": "2.0",
                "basePath": "/",
                "info": {"version": "0.1", "title": "AI Gateway"},
                "schemes": ["http"],
                "paths": {
                    "/chat": {
                        "post": {
                            "operationId": "chat",
                            "x-bk-apigateway-resource": {
                                "kind": "ai",
                                "backend": {"name": backend.name},
                            },
                        }
                    }
                },
            }
        )

        response = request_view(
            method="POST",
            view_name="openapi.resource.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={"content": content, "delete": False},
            gateway=fake_gateway,
        )

        assert response.status_code == 200, response.json()
        resource = Resource.objects.get(gateway=fake_gateway, name="chat")
        assert resource.kind == ResourceKindEnum.AI.value
        assert Proxy.objects.get(resource=resource).config == {}

    def test_sync(
        self,
        request_view,
        fake_gateway,
        fake_default_backend,
        fake_resource_swagger,
        fake_resource,
        fake_resource_echo,
        ignore_related_app_permission,
    ):
        resp = request_view(
            method="POST",
            view_name="openapi.resource.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "content": fake_resource_swagger,
                "delete": True,
            },
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
        assert len(result["data"]["added"]) == 1
        assert len(result["data"]["deleted"]) == 1
        assert len(result["data"]["updated"]) == 1

    def test_sync_with_err_swagger(
        self,
        request_view,
        fake_gateway,
        fake_default_backend,
        fake_err_resource_swagger,
        ignore_related_app_permission,
    ):
        resp = request_view(
            method="POST",
            view_name="openapi.resource.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "content": fake_err_resource_swagger,
                "delete": True,
            },
            gateway=fake_gateway,
        )
        assert resp.status_code != 200

    def test_sync_gen_doc(
        self,
        request_view,
        fake_gateway,
        fake_default_backend,
        fake_resource_swagger,
        fake_resource,
        fake_resource_echo,
        ignore_related_app_permission,
    ):
        resp = request_view(
            method="POST",
            view_name="openapi.resource.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "content": fake_resource_swagger,
                "delete": True,
                "doc_language": "en",
            },
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
        assert len(result["data"]["added"]) == 1
        assert len(result["data"]["deleted"]) == 1
        assert len(result["data"]["updated"]) == 1

        assert len(ResourceDoc.objects.filter(gateway_id=fake_gateway.id, language="en").all()) == 2

    def test_sync_with_null_doc_language(
        self,
        request_view,
        fake_gateway,
        fake_default_backend,
        fake_resource_swagger,
        fake_resource,
        fake_resource_echo,
        ignore_related_app_permission,
    ):
        data_dic = {"content": fake_resource_swagger, "delete": True}
        raw_data = '{"doc_language":null}'
        raw_dict = json.loads(raw_data)
        data_dic["doc_language"] = raw_dict["doc_language"]
        resp = request_view(
            method="POST",
            view_name="openapi.resource.sync",
            path_params={"gateway_name": fake_gateway.name},
            data=data_dic,
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
        assert len(result["data"]["added"]) == 1
        assert len(result["data"]["deleted"]) == 1
        assert len(result["data"]["updated"]) == 1

        assert len(ResourceDoc.objects.filter(gateway_id=fake_gateway.id, language="en").all()) == 0
