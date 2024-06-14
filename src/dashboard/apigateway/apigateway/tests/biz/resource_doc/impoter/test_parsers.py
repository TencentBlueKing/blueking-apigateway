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

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.resource_doc.exceptions import NoResourceDocError
from apigateway.biz.resource_doc.importer.models import ArchiveDoc
from apigateway.biz.resource_doc.importer.parsers import ArchiveParser, BaseParser, OpenAPIParser
from apigateway.core.models import Resource


class TestBaseParser:
    def test_enrich_docs(self, fake_resource_doc, faker):
        fake_gateway = fake_resource_doc.gateway
        fake_resource = Resource.objects.get(id=fake_resource_doc.resource_id)
        parser = BaseParser(fake_gateway.id)

        docs = [
            ArchiveDoc(
                resource_name="no_exist",
                language=DocLanguageEnum.ZH,
                content=faker.pystr(),
            )
        ]
        parser._enrich_docs(docs)
        assert docs[0].resource is None
        assert docs[0].resource_doc is None
        assert docs[0].content_changed is True

        docs = [
            ArchiveDoc(
                resource_name=fake_resource.name,
                language=DocLanguageEnum.ZH,
                content="new content",
            )
        ]
        parser._enrich_docs(docs)
        assert docs[0].resource == fake_resource
        assert docs[0].resource_doc == fake_resource_doc
        assert docs[0].content_changed is True

        docs = [
            ArchiveDoc(
                resource_name=fake_resource.name,
                language=DocLanguageEnum.ZH,
                content=fake_resource_doc.content,
            )
        ]
        parser._enrich_docs(docs)
        assert docs[0].content_changed is False


class TestArchiveParser:
    @pytest.mark.parametrize(
        "files, expected",
        [
            (
                {
                    "zh/get_user.md": "/path/to/zh/get_user.md",
                    "en/get_user.md": "/path/to/en/get_user.md",
                    "zh/create_user.md.j2": "/path/to/zh/create_user.md.j2",
                    "zz/get_user.md": "/path/to/zz/get_user.md",
                    "zh/get_user.txt": "/path/to/zh/get_user.txt",
                },
                [
                    ArchiveDoc(
                        language=DocLanguageEnum("zh"),
                        resource_name="get_user",
                        filename="zh/get_user.md",
                        content="",
                    ),
                    ArchiveDoc(
                        language=DocLanguageEnum("en"),
                        resource_name="get_user",
                        filename="en/get_user.md",
                        content="",
                    ),
                    ArchiveDoc(
                        language=DocLanguageEnum("zh"),
                        resource_name="create_user",
                        filename="zh/create_user.md.j2",
                        content="",
                    ),
                ],
            )
        ],
    )
    def test_parse(self, mocker, files, expected):
        mocker.patch(
            "apigateway.biz.resource_doc.importer.parsers.Jinja2ToMarkdownGenerator.generate_doc_content",
            return_value="",
        )
        result = ArchiveParser(1)._parse(files)
        assert result == expected

    def test_parse__error(self):
        with pytest.raises(NoResourceDocError):
            ArchiveParser(1)._parse({})

    def test_filter_files(self):
        files = {
            "get_user.md": "",
            "en/get_user.md": "",
            "docs/en/get_user.md": "",
            "other/docs/en/get_user.md": "",
        }
        result = ArchiveParser(1)._filter_files(files)
        assert result == {
            "en/get_user.md": "",
            "docs/en/get_user.md": "",
        }

    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("get_user.md", None),
            ("zh/get_user.md", "zh"),
            ("en/get_user.md", "en"),
            ("zz/get_user.md", None),
            ("docs/zh/get_user.md", "zh"),
            ("other/docs/zh/get_user.md", "zh"),
        ],
    )
    def test_extract_language(self, filename, expected):
        result = ArchiveParser(1)._extract_language(filename)
        assert result == expected

    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("zh/get_user.md", "get_user"),
            ("en/get_user.md", "get_user"),
            ("zh/get_user.md.j2", "get_user"),
            ("zz/get_user.txt", None),
            ("docs/zh/get_user.md", "get_user"),
            ("other/docs/zh/get_user.md", "get_user"),
        ],
    )
    def test_extract_resource_name(self, filename, expected):
        result = ArchiveParser(1)._extract_resource_name(filename)
        assert result == expected


class TestSwagger:
    def test_parse(self, fake_gateway, fake_resource_swagger, fake_default_backend):
        docs = OpenAPIParser(fake_gateway.id)._parse(fake_resource_swagger, DocLanguageEnum.ZH)

        assert docs[0].resource_name == "http_get_mapping_user_id"
        assert docs[0].language == DocLanguageEnum.ZH
        assert docs[0].content != ""
        assert docs[0].openapi != ""
