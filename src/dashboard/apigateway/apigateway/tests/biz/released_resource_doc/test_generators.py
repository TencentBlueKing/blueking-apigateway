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

from apigateway.biz.released_resource import ReleasedResourceData
from apigateway.biz.released_resource_doc.generators import DocGenerator
from apigateway.biz.released_resource_doc.released_resource_doc import DummyResourceDocData, ReleasedResourceDocData
from apigateway.core.models import Stage


class TestDocGenerator:
    def test_get_doc_with_release_doc(self, fake_gateway, fake_released_resource, fake_released_resource_doc):
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
            language="zh",
        )
        doc = generator.get_doc()
        assert doc["content"]
        assert doc["updated_time"]

    def test_get_doc_with_dummy_doc(self, fake_gateway, fake_released_resource, fake_released_resource_doc):
        resource_data = ReleasedResourceData.from_data(fake_released_resource.data)
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
