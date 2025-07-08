#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from apigateway.apis.web.resource_doc.serializers import (
    DocArchiveParseOutputSLZ,
    DocImportByArchiveInputSLZ,
)
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.core.models import Resource


class TestDocArchiveParseOutputSLZ:
    @pytest.mark.parametrize(
        "doc, expected",
        [
            (
                {
                    "filename": "en/get_user.md",
                    "language": DocLanguageEnum("en"),
                    "content_changed": True,
                    "resource": None,
                    "resource_doc": None,
                },
                {
                    "filename": "en/get_user.md",
                    "language": "en",
                    "content_changed": True,
                    "resource": None,
                    "resource_doc": None,
                },
            ),
            (
                {
                    "filename": "en/get_user.md",
                    "language": DocLanguageEnum("en"),
                    "content_changed": False,
                    "resource": {
                        "id": 1,
                        "name": "get_user",
                        "method": "GET",
                        "path": "/user",
                        "description": "",
                    },
                    "resource_doc": {
                        "id": 10,
                        "language": "en",
                    },
                },
                {
                    "filename": "en/get_user.md",
                    "language": "en",
                    "content_changed": False,
                    "resource": {
                        "id": 1,
                        "name": "get_user",
                        "method": "GET",
                        "path": "/user",
                        "description": "",
                    },
                    "resource_doc": {
                        "id": 10,
                        "language": "en",
                    },
                },
            ),
        ],
    )
    def test_to_representation(self, doc, expected):
        if doc["resource"]:
            doc["resource"] = Resource(**doc["resource"])

        if doc["resource_doc"]:
            doc["resource_doc"] = ResourceDoc(**doc["resource_doc"])

        slz = DocArchiveParseOutputSLZ(instance=doc)
        assert slz.data == expected


class TestDocImportByArchiveInputSLZ:
    @pytest.mark.parametrize(
        "selected_resource_docs, expected",
        [
            (
                [
                    {
                        "language": "en",
                        "resource_name": "get_user",
                    }
                ],
                [
                    {
                        "language": "en",
                        "resource_name": "get_user",
                    }
                ],
            )
        ],
    )
    def test_validate_selected_resource_docs(self, mocker, faker, selected_resource_docs, expected):
        slz = DocImportByArchiveInputSLZ(
            data={
                "file": mocker.MagicMock(name=faker.pystr(min_chars=1), size=faker.pyint(min_value=1)),
                "selected_resource_docs": json.dumps(selected_resource_docs),
            },
        )
        slz.is_valid(raise_exception=True)
        assert slz.validated_data["selected_resource_docs"] == expected
