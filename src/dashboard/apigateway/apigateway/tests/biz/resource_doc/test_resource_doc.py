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
from ddf import G

from apigateway.apps.support.models import ResourceDoc
from apigateway.biz.resource_doc.resource_doc import ResourceDocHandler


class TestResourceDocHandler:
    def test_get_resource_doc_tmpl(self):
        result = ResourceDocHandler.get_resource_doc_tmpl("bk-user", "zh")
        assert result != ""

        result = ResourceDocHandler.get_resource_doc_tmpl("bk-user", "en")
        assert result != ""

        result = ResourceDocHandler.get_resource_doc_tmpl("bk-user", "unknown")
        assert result == ""

    def test_get_docs(self, fake_resource):
        result = ResourceDocHandler.get_docs([])
        assert result == {}

        zh_doc = G(ResourceDoc, resource_id=fake_resource.id, gateway=fake_resource.gateway, language="zh")
        result = ResourceDocHandler.get_docs([fake_resource.id])
        assert result == {
            fake_resource.id: [
                {
                    "id": zh_doc.id,
                    "language": "zh",
                }
            ]
        }

        en_doc = G(ResourceDoc, resource_id=fake_resource.id, gateway=fake_resource.gateway, language="en")
        result = ResourceDocHandler.get_docs([fake_resource.id])
        assert result == {
            fake_resource.id: [
                {
                    "id": zh_doc.id,
                    "language": "zh",
                },
                {
                    "id": en_doc.id,
                    "language": "en",
                },
            ]
        }

    def test_get_docs_by_resource(self, fake_resource):
        G(ResourceDoc, resource_id=fake_resource.id, gateway=fake_resource.gateway, language="zh")
        G(ResourceDoc, resource_id=fake_resource.id, gateway=fake_resource.gateway, language="en")

        result = ResourceDocHandler.get_docs_by_resource_ids([])
        assert result == {}

        result = ResourceDocHandler.get_docs_by_resource_ids([fake_resource.id])
        assert len(result[fake_resource.id]) == 2
