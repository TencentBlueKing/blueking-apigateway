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
import json

import pytest
from ddf import G

from apigateway.apps.support.models import (
    APISDK,
    ReleasedResourceDoc,
    ResourceDoc,
    ResourceDocSwagger,
    ResourceDocVersion,
)
from apigateway.core.models import Gateway, Resource, ResourceVersion
from apigateway.tests.utils.testing import create_gateway

pytestmark = pytest.mark.django_db


class TestResourceDocManager:
    def test_get_doc_key_to_id(self):
        gateway = G(Gateway)

        r1 = G(Resource, api=gateway)
        r2 = G(Resource, api=gateway)

        doc1 = G(ResourceDoc, resource_id=r1.id, api=gateway)
        doc2 = G(ResourceDoc, resource_id=r2.id, api=gateway, language="en")

        result = ResourceDoc.objects.get_doc_key_to_id(gateway.id)
        assert result == {
            f"{r1.id}:zh": doc1.id,
            f"{r2.id}:en": doc2.id,
        }

    def test_query_doc_key_to_content(self):
        gateway = G(Gateway)

        r1 = G(Resource, api=gateway)
        r2 = G(Resource, api=gateway)

        doc1 = G(ResourceDoc, resource_id=r1.id, api=gateway, content="content1")
        doc2 = G(ResourceDoc, resource_id=r2.id, api=gateway, content="content2", language="en")

        result = ResourceDoc.objects.query_doc_key_to_content(gateway.id)
        assert result == {
            f"{r1.id}:zh": "content1",
            f"{r2.id}:en": "content2",
        }

    def test_get_doc_languages_of_resources(self):
        gateway = G(Gateway)

        r1 = G(Resource, api=gateway)
        r2 = G(Resource, api=gateway)

        doc1 = G(ResourceDoc, api=gateway, resource_id=r1.id, language="zh")
        doc2 = G(ResourceDoc, api=gateway, resource_id=r2.id, language="en")

        result = ResourceDoc.objects.get_doc_languages_of_resources(gateway.id, [r1.id, r2.id])
        assert result == {
            r1.id: ["zh"],
            r2.id: ["en"],
        }

    def test_filter_docs(self):
        gateway = G(Gateway)
        r = G(Resource, api=gateway)
        doc = G(ResourceDoc, resource_id=r.id, api=gateway)

        assert list(ResourceDoc.objects.filter_docs(gateway.id).values_list("id", flat=True)) == [doc.id]
        assert ResourceDoc.objects.filter_docs(gateway.id, [r.id]).count() == 1
        assert ResourceDoc.objects.filter_docs(gateway.id, []).count() == 0


class TestResourceDocSwaggerManager:
    def test_get_resource_doc_id_to_id(self):
        gateway = G(Gateway)

        doc1 = G(ResourceDoc, api=gateway)
        doc2 = G(ResourceDoc, api=gateway)

        s1 = G(ResourceDocSwagger, api=gateway, resource_doc=doc1)
        s2 = G(ResourceDocSwagger, api=gateway, resource_doc=doc2)

        result = ResourceDocSwagger.objects.get_resource_doc_id_to_id(gateway.id)
        assert result == {
            doc1.id: s1.id,
            doc2.id: s2.id,
        }


class TestAPISDKManager:
    def test_filter_resource_version_ids_has_sdk(self):
        gateway = create_gateway()

        rv_1 = G(ResourceVersion, gateway=gateway)
        rv_2 = G(ResourceVersion, gateway=gateway)
        rv_3 = G(ResourceVersion, gateway=gateway)

        G(APISDK, gateway=gateway, resource_version=rv_1)
        G(APISDK, gateway=gateway, resource_version=rv_3)

        data = [
            {
                "params": {
                    "resource_version_ids": [rv_1.id, rv_2.id, rv_3],
                },
                "expected": [rv_1.id, rv_3.id],
            },
            {
                "params": {
                    "resource_version_ids": [rv_2.id],
                },
                "expected": [],
            },
        ]
        for test in data:
            result = APISDK.objects.filter_resource_version_ids_has_sdk(
                gateway.id,
                test["params"]["resource_version_ids"],
            )
            assert result == test["expected"]

    def test_filter_resource_version_public_latest_sdk(self):
        gateway = create_gateway()

        rv_1 = G(ResourceVersion, gateway=gateway)
        rv_2 = G(ResourceVersion, gateway=gateway)
        rv_3 = G(ResourceVersion, gateway=gateway)

        G(
            APISDK,
            gateway=gateway,
            resource_version=rv_1,
            language="python",
            is_public=True,
        )
        G(
            APISDK,
            gateway=gateway,
            resource_version=rv_1,
            language="python",
            is_public=False,
        )
        sdk3 = G(
            APISDK,
            gateway=gateway,
            resource_version=rv_1,
            language="python",
            is_public=True,
        )
        G(
            APISDK,
            gateway=gateway,
            resource_version=rv_2,
            language="python",
            is_public=False,
        )
        sdk5 = G(
            APISDK,
            gateway=gateway,
            resource_version=rv_3,
            language="python",
            is_public=True,
        )

        result = APISDK.objects.filter_resource_version_public_latest_sdk(
            gateway.id,
            resource_version_ids=[rv_1.id, rv_2.id, rv_3.id],
        )
        assert result == {
            rv_1.id: sdk3,
            rv_3.id: sdk5,
        }


class TestReleasedResourceDocManager:
    def test_get_released_resource_doc(self, fake_gateway):
        # doc exist
        G(ReleasedResourceDoc, gateway=fake_gateway, resource_version_id=1, resource_id=1, data={"content": "test"})
        result = ReleasedResourceDoc.objects.get_released_resource_doc(fake_gateway.id, 1, 1)
        assert result == {"content": "test"}

        # doc not exist
        result = ReleasedResourceDoc.objects.get_released_resource_doc(fake_gateway.id, 1, 2)
        assert result == {}

    def test_get_doc_updated_time(self, fake_resource_version, fake_resource1):
        fake_gateway = fake_resource_version.gateway
        G(
            ReleasedResourceDoc,
            gateway=fake_gateway,
            resource_version_id=fake_resource_version.id,
            resource_id=fake_resource1.id,
            language="zh",
            data={"updated_time": "1970-10-10 12:10:20"},
        )

        result = ReleasedResourceDoc.objects.get_doc_updated_time(
            fake_gateway.id,
            fake_resource_version.id,
            fake_resource1.id,
        )
        assert result == {"zh": "1970-10-10 12:10:20"}


class TestResourceDocVersionManager:
    def test_get_doc_data_by_rv_or_new(self, fake_gateway):
        resource = G(Resource, api=fake_gateway)
        rv = G(ResourceVersion, gateway=fake_gateway)

        G(ResourceDoc, api=fake_gateway, resource_id=resource.id)
        G(
            ResourceDocVersion,
            gateway=fake_gateway,
            resource_version=rv,
            _data=json.dumps([{"resource_id": 1, "language": "zh", "content": "test"}]),
        )

        # new resource-doc-version
        result = ResourceDocVersion.objects.get_doc_data_by_rv_or_new(fake_gateway.id, None)
        assert len(result) == 1

        # resource_version_id not exist
        result = ResourceDocVersion.objects.get_doc_data_by_rv_or_new(fake_gateway.id, rv.id + 1)
        assert result == []

        # resource_version_id exist
        result = ResourceDocVersion.objects.get_doc_data_by_rv_or_new(fake_gateway.id, rv.id)
        assert result == [{"resource_id": 1, "language": "zh", "content": "test"}]

    def test_get_doc_updated_time(self, fake_gateway):
        rv = G(ResourceVersion, gateway=fake_gateway)
        G(
            ResourceDocVersion,
            gateway=fake_gateway,
            resource_version=rv,
            _data=json.dumps(
                [{"resource_id": 1, "language": "zh", "content": "test", "updated_time": "1970-10-10 12:10:20"}]
            ),
        )

        result = ResourceDocVersion.objects.get_doc_updated_time(fake_gateway.id, rv.id)
        assert result == {1: {"zh": "1970-10-10 12:10:20"}}
