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

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import translation


class TestSDKListApi:
    def test_list_without_login(self, fake_gateway, fake_sdk):
        resp = Client().get(
            reverse("docs.gateway.gateway_sdk.list", kwargs={"gateway_name": fake_gateway.name}),
            data={
                "language": fake_sdk.language,
            },
        )

        assert resp.status_code == 401

    def test_list(self, request_view, fake_gateway, fake_stage, fake_sdk, fake_release):
        resp = request_view(
            method="GET",
            view_name="docs.gateway.gateway_sdk.list",
            path_params={
                "gateway_name": fake_gateway.name,
            },
            data={
                "language": fake_sdk.language,
            },
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 1
        assert result["data"][0]["stage"]
        assert result["data"][0]["resource_version"]
        assert result["data"][0]["sdk"]


class TestSDKUsageExampleApi:
    def test_retrieve_without_login(self, fake_gateway):
        resp = Client().get(
            reverse("docs.gateway.gateway_sdk.retrieve_usage_example", kwargs={"gateway_name": fake_gateway.name}),
            data={
                "language": "python",
                "stage_name": "prod",
                "resource_name": "get_color",
            },
        )

        assert resp.status_code == 401

    @pytest.mark.parametrize(
        ("language", "artifact_type"),
        [
            ("python", "wheel"),
            ("java", "distribution_zip"),
            ("go", "go_zip"),
            ("javascript", "npm_tgz"),
            ("rust", "crate"),
        ],
    )
    def test_retrieve(self, request_view, fake_gateway, fake_sdk, language, artifact_type):
        fake_sdk.language = language
        fake_sdk.name = "bkapi-demo"
        fake_sdk.url = "https://repo.example.com/sdk-package"
        fake_sdk._config = json.dumps(
            {
                "project_name": "git.example.com/bkapi/demo",
                "package_name": "bkapi_demo",
                "artifacts": [
                    {
                        "distributor": "bkrepo_generic",
                        "type": artifact_type,
                        "filename": "sdk-package",
                        "url": fake_sdk.url,
                    }
                ],
            }
        )
        fake_sdk.save(update_fields=["language", "name", "url", "_config"])
        resp = request_view(
            method="GET",
            view_name="docs.gateway.gateway_sdk.retrieve_usage_example",
            path_params={
                "gateway_name": fake_gateway.name,
            },
            data={
                "language": language,
                "stage_name": "prod",
                "resource_name": "get_color",
            },
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        content = result["data"]["content"]
        assert "X-Bkapi-Authorization" in content
        assert "https://repo.example.com/sdk-package" in content
        assert "/prod" in content
        for removed in ("bkapi.bk_apigateway.shortcuts", "get_client_by_request", "bkapi-client-generator", "golang"):
            assert removed not in content

    def test_retrieve_ignores_legacy_sdk(self, request_view, fake_gateway, fake_sdk):
        fake_sdk._config = json.dumps({"python": {"repository": "default"}})
        fake_sdk.save(update_fields=["_config"])

        resp = request_view(
            method="GET",
            view_name="docs.gateway.gateway_sdk.retrieve_usage_example",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "language": "python",
                "stage_name": "prod",
                "resource_name": "get_color",
            },
            gateway=fake_gateway,
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["content"] == ""

    @pytest.mark.parametrize("language_code", ["en", "zh-hans"])
    def test_retrieve_java_uses_generated_invoker_package(self, request_view, fake_gateway, fake_sdk, language_code):
        fake_sdk.language = "java"
        fake_sdk._config = json.dumps(
            {
                "project_name": "bkapi-demo",
                "package_name": "com.tencent.bkapi.demo",
                "artifacts": [],
            }
        )
        fake_sdk.save(update_fields=["language", "_config"])

        with translation.override(language_code):
            resp = request_view(
                method="GET",
                view_name="docs.gateway.gateway_sdk.retrieve_usage_example",
                path_params={"gateway_name": fake_gateway.name},
                data={
                    "language": "java",
                    "stage_name": "prod",
                    "resource_name": "get_color",
                },
                gateway=fake_gateway,
            )

        content = resp.json()["data"]["content"]
        assert "import com.tencent.bkapi.demo.ApiClient;" in content
        assert "import com.tencent.bkapi.demo.Configuration;" in content
        assert "org.openapitools.client" not in content

    @pytest.mark.parametrize("language_code", ["en", "zh-hans"])
    def test_retrieve_go_uses_module_path_and_package_name(self, request_view, fake_gateway, fake_sdk, language_code):
        fake_sdk.language = "go"
        fake_sdk._config = json.dumps(
            {
                "project_name": "git.example.com/bkapi/demo",
                "package_name": "bkapi_demo",
                "artifacts": [],
            }
        )
        fake_sdk.save(update_fields=["language", "_config"])

        with translation.override(language_code):
            resp = request_view(
                method="GET",
                view_name="docs.gateway.gateway_sdk.retrieve_usage_example",
                path_params={"gateway_name": fake_gateway.name},
                data={
                    "language": "go",
                    "stage_name": "prod",
                    "resource_name": "get_color",
                },
                gateway=fake_gateway,
            )

        content = resp.json()["data"]["content"]
        assert 'bkapi_demo "git.example.com/bkapi/demo"' in content
        assert "cfg := bkapi_demo.NewConfiguration()" in content
        assert "client := bkapi_demo.NewAPIClient(cfg)" in content
