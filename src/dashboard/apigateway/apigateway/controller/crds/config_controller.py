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
from django.conf import settings

from apigateway.controller.crds.v1beta1.models.gateway_config import ConfigController, ConfigControllerAuth
from apigateway.core.micro_gateway_config import MicroGatewayJWTAuth
from apigateway.core.models import MicroGateway


def create_config_controller(micro_gateway: MicroGateway):
    jwt_auth = MicroGatewayJWTAuth.from_micro_gateway_config(micro_gateway.config)
    # endpoints + base_path 为微网关实例访问网关数据的网关接口地址前缀，
    # 例如：endpoints=["http://bkapi.example.com/api/bk-apigateway"], base_path="/prod"
    # 访问地址前缀即为：http://bkapi.example.com/api/bk-apigateway/prod
    return ConfigController(
        endpoints=[settings.BK_API_URL_TMPL.format(api_name="bk-apigateway")],
        base_path=settings.EDGE_CONTROLLER_API_BASE_PATH,
        jwt_auth=ConfigControllerAuth(
            secret=jwt_auth.secret_key,
        ),
    )
