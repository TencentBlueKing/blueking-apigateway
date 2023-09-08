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
from apigateway.apis.web.docs.gateway.gateway.serializers import GatewayOutputSLZ
from apigateway.common.contexts import GatewayAuthContext


class TestGatewayOutputSLZ:
    def test_to_representation(self, settings, fake_gateway):
        settings.BK_API_URL_TMPL = "http://{api_name}.example.com"

        slz = GatewayOutputSLZ(
            fake_gateway,
            context={
                "gateway_auth_configs": GatewayAuthContext().get_gateway_id_to_auth_config([fake_gateway.id]),
            },
        )

        assert slz.data["is_official"] is False
        assert slz.data["api_url"] == f"http://{fake_gateway.name}.example.com"
