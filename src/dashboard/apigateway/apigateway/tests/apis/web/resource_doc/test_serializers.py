import json

import pytest
from ddf import G
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.resource_doc.serializers import (
    ResourceDocArchiveParseOutputSLZ,
    ResourceDocImportByArchiveInputSLZ,
    ResourceDocInputSLZ,
)
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.core.models import Resource


class TestResourceDocInputSLZ:
    def test_validate_language(self, faker, fake_gateway):
        resource_id = faker.pyint(min_value=1)
        resource_doc = G(ResourceDoc, api=fake_gateway, resource_id=resource_id, language="zh")

        # create
        slz = ResourceDocInputSLZ(data={}, context={"gateway_id": fake_gateway.id, "resource_id": resource_id})
        assert slz.validate_language("en") == "en"

        # create, failed
        with pytest.raises(ValidationError):
            assert slz.validate_language("zh") == "zh"

        # update
        G(ResourceDoc, api=fake_gateway, resource_id=resource_id, language="en")
        slz = ResourceDocInputSLZ(
            instance=resource_doc, data={}, context={"gateway_id": fake_gateway.id, "resource_id": resource_id}
        )
        assert slz.validate_language("zh") == "zh"

        # update, failed
        with pytest.raises(ValidationError):
            assert slz.validate_language("en")


class TestResourceDocArchiveParseOutputSLZ:
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

        slz = ResourceDocArchiveParseOutputSLZ(instance=doc, many=True)
        assert slz.data == [expected]


class TestResourceDocImportByArchiveInputSLZ:
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
    def test_validate_selected_resource_docs(self, fake_tgz_file, selected_resource_docs, expected):
        slz = ResourceDocImportByArchiveInputSLZ(
            data={
                "file": fake_tgz_file,
                "selected_resource_docs": json.dumps(selected_resource_docs),
            }
        )
        slz.is_valid(raise_exception=True)
        assert slz.validated_data["selected_resource_docs"] == expected
