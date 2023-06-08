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
from rest_framework import serializers as drf_serializers

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.apps.support.resource_doc import serializers
from apigateway.core.models import Gateway, Resource


class TestResourceDocSLZ:
    @pytest.mark.parametrize(
        "instance, language, expected",
        [
            (
                None,
                "zh",
                "zh",
            ),
            (
                {"language": "zh"},
                "zh",
                "zh",
            ),
            (
                {"language": "zh"},
                "en",
                "zh",
            ),
        ],
    )
    def test_validate_language(self, mocker, faker, instance, language, expected):
        if instance:
            instance = mocker.MagicMock(**instance)

        slz = serializers.ResourceDocSLZ(
            instance=instance,
            data={
                "type": "markdown",
                "language": language,
                "content": faker.pystr(),
            },
            context={
                "api_id": 0,
                "resource_id": 0,
            },
        )
        slz.is_valid()

        assert slz.validated_data["language"] == expected

    def test_validate_language_error(self, faker):
        gateway = G(Gateway)
        resource = G(Resource, api=gateway)
        G(ResourceDoc, resource_id=resource.id, api=gateway, language="zh")

        slz = serializers.ResourceDocSLZ(
            data={
                "type": "markdown",
                "language": "zh",
                "content": faker.pystr(),
            },
            context={
                "api_id": gateway.id,
                "resource_id": resource.id,
            },
        )

        with pytest.raises(drf_serializers.ValidationError):
            slz.is_valid(raise_exception=True)


class TestArchiveDocParseResultSLZ:
    @pytest.mark.parametrize(
        "instance, resource_id_to_object, expected",
        [
            (
                {
                    "filename": "en/get_user.md",
                    "language": DocLanguageEnum("en"),
                    "resource_id": None,
                    "resource_name": "get_user",
                    "resource_doc_id": None,
                    "resource_doc_content_changed": True,
                },
                {},
                {
                    "filename": "en/get_user.md",
                    "id": None,
                    "name": "get_user",
                    "method": "",
                    "path": "",
                    "description": "",
                    "resource_doc_id": None,
                    "resource_doc_language": "en",
                    "resource_doc_content_changed": True,
                },
            ),
            (
                {
                    "filename": "en/get_user.md",
                    "language": DocLanguageEnum("en"),
                    "resource_id": 1,
                    "resource_name": "get_user",
                    "resource_doc_id": None,
                    "resource_doc_content_changed": True,
                },
                {
                    1: {
                        "method": "GET",
                        "path": "/user",
                        "description": "test",
                    }
                },
                {
                    "filename": "en/get_user.md",
                    "id": 1,
                    "name": "get_user",
                    "method": "GET",
                    "path": "/user",
                    "description": "test",
                    "resource_doc_id": None,
                    "resource_doc_language": "en",
                    "resource_doc_content_changed": True,
                },
            ),
        ],
    )
    def test_to_representation(self, mocker, instance, resource_id_to_object, expected):
        instance = mocker.MagicMock(**instance)
        resource_id_to_object = {
            resource_id: mocker.MagicMock(**obj) for resource_id, obj in resource_id_to_object.items()
        }

        slz = serializers.ArchiveDocParseResultSLZ(
            instance=[instance],
            many=True,
            context={
                "resource_id_to_object": resource_id_to_object,
            },
        )
        assert slz.data == [expected]


class TestImportResourceDocsByArchiveSLZ:
    @pytest.mark.parametrize(
        "selected_resource_docs, resource_name_to_id, expected",
        [
            (
                [
                    {
                        "language": "en",
                        "resource_name": "get_user",
                    }
                ],
                {
                    "get_user": 1,
                },
                [
                    {
                        "language": "en",
                        "resource_id": 1,
                        "resource_name": "get_user",
                    }
                ],
            )
        ],
    )
    def test_validate_selected_resource_docs(self, mocker, selected_resource_docs, resource_name_to_id, expected):
        slz = serializers.ImportResourceDocsByArchiveSLZ(context={"resource_name_to_id": resource_name_to_id})
        result = slz.validate_selected_resource_docs(selected_resource_docs)
        assert result == expected


class TestImportResourceDocsBySwaggerSLZ:
    @pytest.mark.parametrize(
        "data, resource_name_to_id, expected",
        [
            (
                {
                    "selected_resource_docs": [
                        {
                            "language": "en",
                            "resource_name": "get_user",
                        }
                    ],
                    "swagger": "test",
                },
                {
                    "get_user": 1,
                },
                {
                    "selected_resource_docs": [
                        {
                            "language": "en",
                            "resource_id": 1,
                            "resource_name": "get_user",
                        }
                    ],
                    "language": "en",
                    "swagger": "test",
                },
            ),
        ],
    )
    def test_validate(self, data, resource_name_to_id, expected):
        slz = serializers.ImportResourceDocsBySwaggerSLZ(
            data=data, context={"resource_name_to_id": resource_name_to_id}
        )
        slz.is_valid()
        assert slz.validated_data == expected

    @pytest.mark.parametrize(
        "data, resource_name_to_id",
        [
            (
                {
                    "selected_resource_docs": [
                        {
                            "language": "en",
                            "resource_name": "get_user",
                        }
                    ],
                    "swagger": "test",
                },
                {},
            ),
        ],
    )
    def test_validate_error(self, data, resource_name_to_id):
        with pytest.raises(drf_serializers.ValidationError):
            slz = serializers.ImportResourceDocsBySwaggerSLZ(
                data=data, context={"resource_name_to_id": resource_name_to_id}
            )
            slz.is_valid(raise_exception=True)
