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

from apigateway.apps.resource.swagger.swagger import SwaggerManager
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.resource_doc.import_doc.docs import ArchiveDoc, SwaggerDoc
from apigateway.apps.support.resource_doc.import_doc.parsers import ArchiveParser, SwaggerParser
from apigateway.core.constants import SwaggerFormatEnum


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
                        resource_doc_path="/path/to/zh/get_user.md",
                    ),
                    ArchiveDoc(
                        language=DocLanguageEnum("en"),
                        resource_name="get_user",
                        filename="en/get_user.md",
                        resource_doc_path="/path/to/en/get_user.md",
                    ),
                    ArchiveDoc(
                        language=DocLanguageEnum("zh"),
                        resource_name="create_user",
                        filename="zh/create_user.md.j2",
                        resource_doc_path="/path/to/zh/create_user.md.j2",
                    ),
                ],
            )
        ],
    )
    def test_parse(self, files, expected):
        result = ArchiveParser().parse(files)
        assert result == expected

    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("zh/get_user.md", "zh"),
            ("en/get_user.md", "en"),
            ("zz/get_user.md", "zz"),
        ],
    )
    def test_extract_language(self, filename, expected):
        result = ArchiveParser()._extract_language(filename)
        assert result == expected

    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("zh/get_user.md", "get_user"),
            ("en/get_user.md", "get_user"),
            ("zh/get_user.md.j2", "get_user"),
            ("zz/get_user.txt", None),
        ],
    )
    def test_extract_resource_name(self, filename, expected):
        result = ArchiveParser()._extract_resource_name(filename)
        assert result == expected


class TestSwaggerParser:
    def test_parse(self, mocker):
        mocker.patch(
            "apigateway.apps.support.resource_doc.import_doc.parsers.SwaggerParser._expand_swagger", return_value=""
        )
        mocker.patch(
            "apigateway.apps.support.resource_doc.import_doc.parsers.SwaggerManager.load_from_swagger",
            return_value=mocker.MagicMock(
                **{
                    "validate.return_value": None,
                    "get_paths.return_value": {
                        "/user": {
                            "get": {
                                "operationId": "get_user",
                            }
                        }
                    },
                }
            ),
        )

        result = SwaggerParser().parse("swagger", DocLanguageEnum.ZH)
        assert result == [
            SwaggerDoc(
                language=DocLanguageEnum.ZH,
                resource_name="get_user",
                resource_doc_swagger=SwaggerManager.to_swagger(
                    paths={
                        "/user": {
                            "get": {
                                "operationId": "get_user",
                            }
                        }
                    },
                    title="get_user",
                    swagger_format=SwaggerFormatEnum.YAML,
                ),
            )
        ]
