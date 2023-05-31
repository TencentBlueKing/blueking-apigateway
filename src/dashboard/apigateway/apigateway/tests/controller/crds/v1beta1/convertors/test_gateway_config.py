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
from apigateway.core.micro_gateway_config import MicroGatewayJWTAuth


class TestGatewayConfigConvertor:
    def test_convert(
        self,
        settings,
        edge_gateway,
        edge_gateway_stage,
        micro_gateway,
        fake_gateway_config_convertor,
    ):
        settings.BK_API_URL_TMPL = "http://bkapi.example.com/{api_name}"
        settings.EDGE_CONTROLLER_API_BASE_PATH = "/test"

        jwt_auth = MicroGatewayJWTAuth.from_micro_gateway_config(micro_gateway.config)
        config = fake_gateway_config_convertor.convert()

        assert config.spec.name == edge_gateway.name

        metadata = config.metadata
        assert 0 < len(metadata.name) <= 64

        assert metadata.get_label("gateway") == edge_gateway.name
        assert metadata.get_label("stage") == edge_gateway_stage.name

        spec = config.spec
        assert spec.instance_id == str(micro_gateway.id)
        assert spec.controller.endpoints == ["http://bkapi.example.com/bk-apigateway"]
        assert spec.controller.base_path == "/test"
        assert spec.controller.jwt_auth.secret == jwt_auth.secret_key
