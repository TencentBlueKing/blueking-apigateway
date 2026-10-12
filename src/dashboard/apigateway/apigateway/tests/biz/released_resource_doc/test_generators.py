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

from apigateway.biz.released_resource import ReleasedResourceData
from apigateway.biz.released_resource_doc import DocGenerator, DummyResourceDocData, ReleasedResourceDocData, constants
from apigateway.core.models import Stage


class TestDocGenerator:
    def test_get_doc_with_release_doc(self, fake_gateway, fake_released_resource, fake_released_resource_doc):
        resource_data = ReleasedResourceData.from_data(fake_released_resource.data)
        doc_data = ReleasedResourceDocData.from_data(fake_released_resource_doc.data)
        doc_data.content = "### 请求参数\n正文内容"

        stage_name = "prod"
        # fake a stage with name => for get_resource_url_tmpl
        G(Stage, gateway=fake_gateway, status=1, name=stage_name, description="fake description")

        generator = DocGenerator(
            gateway=fake_gateway,
            stage_name=stage_name,
            resource_data=resource_data,
            doc_data=doc_data,
            language="zh",
        )
        doc = generator.get_doc()
        assert doc["content"]
        assert doc["updated_time"]
        assert doc["method"] == resource_data.method
        assert doc["resource_url"] in doc["content"]
        assert doc["auth_content"] in doc["content"]
        assert doc["body_content"] == doc_data.content
        assert doc_data.content in doc["content"]

        # MCP callers intentionally omit the common authentication section.
        generator.with_common_request_params_part = False
        doc = generator.get_doc()
        assert doc["auth_content"] == ""
        assert "X-Bkapi-Authorization" not in doc["content"]
        assert doc["body_content"] == doc_data.content

    def test_get_doc_with_dummy_doc(self, fake_gateway, fake_released_resource, fake_released_resource_doc):
        # Older snapshots may not contain plugins, and resources may have no body or auth requirements.
        fake_released_resource.data.pop("plugins", None)
        resource_data = ReleasedResourceData.from_data(fake_released_resource.data)
        resource_data.verified_app_required = resource_data.verified_user_required = False
        doc_data = DummyResourceDocData.create("zh")

        stage_name = "prod"
        # fake a stage with name => for get_resource_url_tmpl
        G(Stage, gateway=fake_gateway, status=1, name=stage_name, description="fake description")

        generator = DocGenerator(
            gateway=fake_gateway,
            stage_name=stage_name,
            resource_data=resource_data,
            doc_data=doc_data,
            language="zh",
        )
        doc = generator.get_doc()
        assert doc["content"]
        assert not doc["updated_time"]
        assert doc["auth_content"] == doc["body_content"] == ""
        assert doc["resource_url"] in doc["content"]

    @pytest.mark.parametrize(
        "template_name,plugins,auth_required,expected,unexpected",
        [
            (
                "ZH",
                [{"type": "bk-access-token-source", "config": {}}],
                True,
                [
                    "| Authorization | string | 二选一 |",
                    "| X-Bkapi-Authorization | string | 二选一 |",
                    "| bk_app_code",
                    "\n\n也支持通过 `X-Bkapi-Authorization` 请求头传递认证信息。\n\n",
                ],
                ["| X-Bk-Username |", "| X-Bk-Tenant-Id |"],
            ),
            (
                "ZH_MULTI_TENANT",
                [
                    {"type": "bk-access-token-source", "config": {"source": "api_key", "allow_fallback": False}},
                    {"type": "bk-username-required", "config": None},
                ],
                True,
                ["| X-API-KEY | string | 是 |", "| X-Bk-Username | string | 是 |", "| X-Bk-Tenant-Id | string | 是 |"],
                ["| X-Bkapi-Authorization |", "| bk_app_code"],
            ),
            (
                "EN",
                [{"type": "bk-username-required", "config": None}],
                False,
                ["| X-Bk-Username | string | Yes |", "X-Bk-Username: {username}"],
                ["| bk_app_code", "| X-Bk-Tenant-Id |"],
            ),
            (
                "EN_MULTI_TENANT",
                [{"type": "bk-access-token-source", "config": {"source": "api_key", "allow_fallback": True}}],
                True,
                [
                    "| X-API-KEY | string | Either one |",
                    "| X-Bkapi-Authorization | string | Either one |",
                    "| X-Bk-Tenant-Id | string | Yes |",
                    "| bk_app_code",
                ],
                ["| X-Bk-Username |"],
            ),
            (
                "ZH_MULTI_TENANT",
                [],
                True,
                ["| X-Bk-Tenant-Id | string | 是 |", "| bk_app_code", "| bk_app_secret"],
                ["| Authorization |", "| X-API-KEY |", "| X-Bk-Username |"],
            ),
        ],
        ids=["default-bearer", "strict-api-key", "username-only", "api-key-fallback", "tenant-without-plugins"],
    )
    def test_plugin_authentication(
        self,
        mocker,
        fake_gateway,
        fake_stage,
        fake_released_resource,
        template_name,
        plugins,
        auth_required,
        expected,
        unexpected,
    ):
        language = template_name.split("_")[0].lower()
        template = getattr(constants, f"BKAPI_AUTHORIZATION_DESCRIPTION_{template_name}")
        mocker.patch.dict(constants.BKAPI_AUTHORIZATION_DESCRIPTIONS, {language: template})
        snapshot = {**fake_released_resource.data, "plugins": plugins}
        data = ReleasedResourceData.from_data(snapshot)
        data.verified_app_required = data.verified_user_required = auth_required
        content = DocGenerator(
            fake_gateway,
            fake_stage.name,
            data,
            DummyResourceDocData.create(language),
            language,
        ).get_doc()["auth_content"]
        for text in expected:
            assert text in content
        for text in unexpected:
            assert text not in content
        if "| bk_app_code" in content:
            for header in ("X-Bkapi-Authorization", "X-Bk-Username", "X-Bk-Tenant-Id"):
                if f"| {header} |" in content:
                    assert content.index(f"| {header} |") < content.index("| bk_app_code")

    @pytest.mark.parametrize("language", ["zh", "en"])
    def test_get_resource_url_part(self, fake_gateway, fake_released_resource, fake_released_resource_doc, language):
        resource_data = ReleasedResourceData.from_data(fake_released_resource.data)
        doc_data = ReleasedResourceDocData.from_data(fake_released_resource_doc.data)

        stage_name = "prod"
        # fake a stage with name => for get_resource_url_tmpl
        G(Stage, gateway=fake_gateway, status=1, name=stage_name, description="fake description")

        generator = DocGenerator(
            gateway=fake_gateway,
            stage_name=stage_name,
            resource_data=resource_data,
            doc_data=doc_data,
            language=language,
        )

        part = generator._get_resource_url_part()
        assert part

    @pytest.mark.parametrize("language", ["zh", "en"])
    def test_get_common_request_params_part(
        self, fake_gateway, fake_released_resource, fake_released_resource_doc, language
    ):
        resource_data = ReleasedResourceData.from_data(fake_released_resource.data)
        doc_data = ReleasedResourceDocData.from_data(fake_released_resource_doc.data)

        generator = DocGenerator(
            gateway=fake_gateway,
            stage_name="prod",
            resource_data=resource_data,
            doc_data=doc_data,
            language=language,
        )

        part = generator._get_common_request_params_part()
        assert part
