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

from django_dynamic_fixture import G

from apigateway.apps.support.models import ResourceDoc, ResourceDocVersion
from apigateway.biz.resource_version import ResourceDocVersionHandler
from apigateway.core.models import Resource, ResourceVersion


class TestResourceDocVersionHandler:
    def test_get_doc_data_by_rv_or_new(self, fake_gateway):
        resource = G(Resource, gateway=fake_gateway)
        rv = G(ResourceVersion, gateway=fake_gateway)

        G(ResourceDoc, gateway=fake_gateway, resource_id=resource.id)
        G(
            ResourceDocVersion,
            gateway=fake_gateway,
            resource_version=rv,
            _data=json.dumps([{"resource_id": 1, "language": "zh", "content": "test"}]),
        )

        # new resource-doc-version
        result = ResourceDocVersionHandler().get_doc_data_by_rv_or_new(fake_gateway.id, None)
        assert len(result) == 1

        # resource_version_id not exist
        result = ResourceDocVersionHandler().get_doc_data_by_rv_or_new(fake_gateway.id, rv.id + 1)
        assert result == []

        # resource_version_id exist
        result = ResourceDocVersionHandler().get_doc_data_by_rv_or_new(fake_gateway.id, rv.id)
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

        result = ResourceDocVersionHandler().get_doc_updated_time(fake_gateway.id, rv.id)
        assert result == {1: {"zh": "1970-10-10 12:10:20"}}
