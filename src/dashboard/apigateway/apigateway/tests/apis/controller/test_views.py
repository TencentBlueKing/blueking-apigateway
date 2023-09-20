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


class TestMicroGatewayInfoViewSet:
    def test_shared_gateway(
        self,
        request_view,
        fake_shared_gateway,
        skip_view_permissions_check,
        fake_gateway,
        fake_stage,
    ):
        response = request_view(
            "GET",
            "apigateway.controller.micro_gateway_info",
            {
                "instance_id": fake_shared_gateway.id,
            },
        )
        result = response.json()
        info = result["data"]

        assert info["name"] == fake_shared_gateway.name

        found = False
        for i in info["related_infos"]:
            if i["gateway_name"] == fake_gateway.name and i["stage_name"] == fake_stage.name:
                found = True
                break

        assert found

    def test_edge_gateway(
        self,
        request_view,
        fake_edge_gateway,
        fake_stage,
        skip_view_permissions_check,
        fake_gateway,
    ):
        response = request_view(
            "GET",
            "apigateway.controller.micro_gateway_info",
            {
                "instance_id": fake_edge_gateway.id,
            },
        )
        result = response.json()
        info = result["data"]

        assert info["name"] == fake_edge_gateway.name

        found = False
        for i in info["related_infos"]:
            if i["gateway_name"] == fake_gateway.name and i["stage_name"] == fake_stage.name:
                found = True
                break

        assert found
