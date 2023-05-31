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

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc, ResourceDocSwagger
from apigateway.apps.support.resource_doc.import_doc.docs import SwaggerDoc
from apigateway.apps.support.resource_doc.import_doc.handlers import DocsHandler
from apigateway.core.models import Gateway, Resource

pytestmark = pytest.mark.django_db


class TestDocsHandler:
    @pytest.mark.parametrize(
        "selected_resource_docs, expected",
        [
            (
                [
                    {
                        "resource_id": 1,
                        "language": "zh",
                    },
                    {
                        "resource_id": 2,
                        "language": "zh",
                    },
                ],
                {"1:zh", "2:zh"},
            ),
            (None, None),
        ],
    )
    def test_post_init(self, selected_resource_docs, expected):
        handler = DocsHandler(1, selected_resource_docs=selected_resource_docs)
        assert handler.selected_resource_doc_keys == expected

    def test_handle(self, mocker):
        mock_save_docs = mocker.patch.object(
            DocsHandler,
            "save_docs",
            return_value=None,
        )
        gateway = G(Gateway)
        resource = G(Resource, api=gateway)

        handler = DocsHandler(gateway_id=gateway.id, allow_overwrite=True)
        docs = [
            SwaggerDoc(
                language=DocLanguageEnum.ZH,
                resource_name=resource.name,
                resource_id=resource.id,
            ),
        ]
        handler.handle(docs)

        mock_save_docs.assert_called_once_with(gateway.id, docs)

    def test_enrich_docs(self):
        gateway = G(Gateway)
        resource = G(Resource, api=gateway)
        resource_doc = G(ResourceDoc, resource_id=resource.id, api=gateway)
        resource_doc_swagger = G(ResourceDocSwagger, resource_doc=resource_doc, api=gateway)

        handler = DocsHandler(gateway_id=gateway.id)
        docs = [
            SwaggerDoc(
                language=DocLanguageEnum.ZH,
                resource_name=resource.name,
            ),
        ]
        docs = handler.enrich_docs(gateway.id, docs)

        assert len(docs) == 1
        assert docs[0].resource_id == resource.id
        assert docs[0].resource_doc_id == resource_doc.id
        assert docs[0].resource_doc_swagger_id == resource_doc_swagger.id

    def test_filter_valid_docs(self, faker):
        handler = DocsHandler(0)
        docs = [SwaggerDoc(language=DocLanguageEnum.ZH, resource_name=faker.pystr())]
        docs = handler.filter_valid_docs(docs)
        assert len(docs) == 0

        docs = [SwaggerDoc(language=DocLanguageEnum.ZH, resource_name=faker.pystr(), resource_id=1)]
        docs = handler.filter_valid_docs(docs)
        assert len(docs) == 1

    @pytest.mark.parametrize(
        "docs, allow_overwrite, selected_language, selected_resource_doc_keys, expected",
        [
            (
                [
                    {
                        "language": DocLanguageEnum.ZH,
                        "resource_name": "test",
                    },
                ],
                True,
                "en",
                None,
                0,
            ),
            (
                [
                    {
                        "language": DocLanguageEnum.ZH,
                        "resource_name": "test",
                        "resource_doc_id": 1,
                    },
                ],
                False,
                "",
                None,
                0,
            ),
            (
                [
                    {
                        "language": DocLanguageEnum.ZH,
                        "resource_name": "test",
                        "resource_id": 1,
                    },
                ],
                False,
                "",
                {"2:zh"},
                0,
            ),
            (
                [
                    {
                        "language": DocLanguageEnum.ZH,
                        "resource_name": "test",
                    },
                ],
                False,
                "",
                None,
                1,
            ),
        ],
    )
    def test_filter_selected_docs(
        self, docs, allow_overwrite, selected_language, selected_resource_doc_keys, expected
    ):
        handler = DocsHandler(0)

        docs = [SwaggerDoc(**doc) for doc in docs]
        docs = handler.filter_selected_docs(docs, allow_overwrite, selected_language, selected_resource_doc_keys)
        assert len(docs) == expected

    def test_save_docs(self, faker, mocker):
        mocker.patch.object(
            SwaggerDoc,
            "resource_doc_markdown",
            new_callable=mocker.PropertyMock(return_value=""),
        )

        gateway = G(Gateway)
        resource = G(Resource, api=gateway)

        handler = DocsHandler(gateway_id=gateway.id)
        doc = SwaggerDoc(resource_id=resource.id, language=DocLanguageEnum.ZH, resource_name=faker.pystr())
        handler.save_docs(gateway.id, [doc])

        id1 = doc.resource_doc_id
        assert id1 != 0

        handler.save_docs(gateway.id, [doc])
        id2 = doc.resource_doc_id
        assert id2 != 0
        assert id1 == id2
