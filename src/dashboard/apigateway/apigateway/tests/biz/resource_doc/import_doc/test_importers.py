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
from apigateway.apps.support.models import ResourceDoc
from apigateway.biz.resource_doc.import_doc.importers import ResourceDocImporter
from apigateway.biz.resource_doc.import_doc.models import ArchiveDoc
from apigateway.core.models import Resource


class TestResourceDocImporter:
    def test_import_docs(self, fake_resource_doc, faker):
        fake_gateway = fake_resource_doc
        fake_resource = Resource.objects.get(id=fake_resource_doc.resource_id)
        resource_2 = G(Resource, api=fake_gateway)

        docs = [
            ArchiveDoc(
                resource_name=fake_resource.name,
                language=fake_resource_doc.language,
                content=faker.pystr(),
                resource=fake_resource,
                resource_doc=fake_resource_doc,
            ),
            ArchiveDoc(
                resource_name=resource_2.name,
                language="zh",
                content=faker.pystr(),
                resource=resource_2,
            ),
            ArchiveDoc(
                resource_name=resource_2.name,
                language="zh",
                content=faker.pystr(),
            ),
        ]

        importer = ResourceDocImporter(fake_gateway, None)
        importer.import_docs(docs)

        assert ResourceDoc.objects.filter(api=fake_gateway).count() == 2

    def test_filter_valid_docs(self, faker, fake_resource):
        importer = ResourceDocImporter(1, None)

        docs = [
            ArchiveDoc(
                language=DocLanguageEnum.ZH,
                resource_name=faker.pystr(),
                content=faker.pystr(),
            )
        ]
        docs = importer._filter_valid_docs(docs)
        assert docs == []

        docs = [
            ArchiveDoc(
                language=DocLanguageEnum.ZH,
                resource_name=faker.pystr(),
                content=faker.pystr(),
                resource=fake_resource,
            )
        ]
        docs = importer._filter_valid_docs(docs)
        assert len(docs) == 1

    @pytest.mark.parametrize(
        "docs, selected_resource_docs, expected",
        [
            (
                [
                    {
                        "language": DocLanguageEnum.ZH,
                        "resource_name": "test",
                    },
                ],
                [
                    {
                        "language": "zh",
                        "resource_name": "test",
                    },
                ],
                1,
            ),
            (
                [
                    {
                        "language": DocLanguageEnum.ZH,
                        "resource_name": "test",
                    },
                ],
                [
                    {
                        "language": "zh",
                        "resource_name": "another",
                    },
                ],
                0,
            ),
            (
                [
                    {
                        "language": DocLanguageEnum.ZH,
                        "resource_name": "test",
                    },
                ],
                None,
                1,
            ),
        ],
    )
    def test_filter_selected_docs(self, faker, docs, selected_resource_docs, expected):
        importer = ResourceDocImporter(1, selected_resource_docs=selected_resource_docs)

        docs = [ArchiveDoc(**docs, content=faker.pystr())]
        docs = importer._filter_selected_docs(docs)

        assert len(docs) == expected

    def test_save_docs(self, faker, fake_resource_doc):
        fake_gateway = fake_resource_doc.api
        fake_resource = Resource.objects.get(id=fake_resource_doc.resource_id)
        resource_2 = G(Resource, api=fake_gateway)

        docs = [
            ArchiveDoc(
                resource_name=fake_resource.name,
                language=DocLanguageEnum(fake_resource_doc.language),
                content=faker.pystr(),
                resource=fake_resource,
                resource_doc=fake_resource_doc,
            ),
            ArchiveDoc(
                resource_name=resource_2.name,
                language=DocLanguageEnum.ZH,
                content=faker.pystr(),
                resource=resource_2,
            ),
        ]

        importer = ResourceDocImporter(fake_gateway.id, None)
        importer._save_docs(docs)

        assert ResourceDoc.objects.filter(api=fake_gateway).count() == 2

    @pytest.mark.parametrize(
        "selected_resource_docs, expected",
        [
            (
                [
                    {
                        "language": "en",
                        "resource_name": "test",
                    },
                    {
                        "language": "zh",
                        "resource_name": "another",
                    },
                ],
                {"en:test", "zh:another"},
            ),
            (
                None,
                None,
            ),
        ],
    )
    def test_get_selected_resource_doc_keys(self, selected_resource_docs, expected):
        importer = ResourceDocImporter(1, selected_resource_docs=selected_resource_docs)
        result = importer._get_selected_resource_doc_keys()
        assert result == expected
