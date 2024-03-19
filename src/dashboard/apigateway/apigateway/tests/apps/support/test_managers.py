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

from apigateway.apps.support.models import (
    ReleasedResourceDoc,
)

pytestmark = pytest.mark.django_db


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
