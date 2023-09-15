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
from django.conf import settings

from apigateway.biz.gateway_related_app import GatewayRelatedAppHandler
from apigateway.common.error_codes import APIError
from apigateway.core.models import GatewayRelatedApp


class TestGatewayRelatedAppHandler:
    def test_add_related_app(self, fake_gateway):
        GatewayRelatedAppHandler.add_related_app(fake_gateway.id, "foo")
        assert GatewayRelatedApp.objects.filter(gateway_id=fake_gateway.id).count() == 1

        GatewayRelatedAppHandler.add_related_app(fake_gateway.id, "foo")
        assert GatewayRelatedApp.objects.filter(gateway_id=fake_gateway.id).count() == 1

        GatewayRelatedAppHandler.add_related_app(fake_gateway.id, "bar")
        assert GatewayRelatedApp.objects.filter(gateway_id=fake_gateway.id).count() == 2

    def test_check_app_gateway_limit(self, fake_gateway):
        settings.API_GATEWAY_RESOURCE_LIMITS["max_gateway_count_per_app_whitelist"]["bk_test"] = 1

        GatewayRelatedAppHandler._check_app_gateway_limit("bk_test")

        GatewayRelatedAppHandler.add_related_app(fake_gateway.id, "bk_test")
        with pytest.raises(APIError):
            GatewayRelatedAppHandler._check_app_gateway_limit("bk_test")

        del settings.API_GATEWAY_RESOURCE_LIMITS["max_gateway_count_per_app_whitelist"]["bk_test"]
        GatewayRelatedAppHandler._check_app_gateway_limit("bk_test")
