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
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.resource.doc.serializers import DocInputSLZ
from apigateway.apps.support.models import ResourceDoc


class TestDocInputSLZ:
    def test_validate_language(self, faker, fake_gateway):
        resource_id = faker.pyint(min_value=1)
        resource_doc = G(ResourceDoc, gateway=fake_gateway, resource_id=resource_id, language="zh")

        # create
        slz = DocInputSLZ(data={}, context={"gateway_id": fake_gateway.id, "resource_id": resource_id})
        assert slz.validate_language("en") == "en"

        # create, failed
        with pytest.raises(ValidationError):
            assert slz.validate_language("zh") == "zh"

        # update
        G(ResourceDoc, gateway=fake_gateway, resource_id=resource_id, language="en")
        slz = DocInputSLZ(
            instance=resource_doc, data={}, context={"gateway_id": fake_gateway.id, "resource_id": resource_id}
        )
        assert slz.validate_language("zh") == "zh"

        # update, failed
        with pytest.raises(ValidationError):
            assert slz.validate_language("en")
