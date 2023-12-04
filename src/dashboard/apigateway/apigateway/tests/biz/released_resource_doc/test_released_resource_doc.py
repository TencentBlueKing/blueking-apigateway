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
from apigateway.biz.released_resource_doc import ReleasedResourceDocHandler
from apigateway.biz.released_resource_doc.released_resource_doc import DummyResourceDocData, ReleasedResourceDocData


class TestReleasedResourceDocData:
    def test_from_data(self):
        result = ReleasedResourceDocData.from_data(
            {
                "language": "zh",
                "content": "hello world",
                "updated_time": "2021-01-01 00:00:00",
            }
        )

        assert result.language == "zh"
        assert result.content == "hello world"
        assert result.updated_time == "2021-01-01 00:00:00"


class TestDummyResourceDocData:
    def test_create(self):
        doc_data = DummyResourceDocData.create("zh")
        assert doc_data.language == "zh"
        assert doc_data.content == ""
        assert doc_data.updated_time == ""


class TestReleasedResourceDocHandler:
    def test_get_released_resource_doc_data(
        self, fake_gateway, fake_stage, fake_released_resource, fake_released_resource_doc
    ):
        resource_data, doc_data = ReleasedResourceDocHandler.get_released_resource_doc_data(
            fake_gateway.id, fake_stage.name, "", fake_released_resource_doc.language
        )
        assert resource_data is None
        assert doc_data is None

        resource_data, doc_data = ReleasedResourceDocHandler.get_released_resource_doc_data(
            fake_gateway.id,
            fake_stage.name,
            fake_released_resource.resource_name,
            "not_exist",
        )
        assert resource_data is not None
        assert doc_data is not None

        resource_data, doc_data = ReleasedResourceDocHandler.get_released_resource_doc_data(
            fake_gateway.id,
            fake_stage.name,
            fake_released_resource.resource_name,
            fake_released_resource_doc.language,
        )
        assert resource_data is not None
        assert doc_data is not None
