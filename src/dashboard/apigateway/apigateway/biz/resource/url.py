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

from apigateway.controller.micro_gateway_config import MicroGatewayHTTPInfo
from apigateway.core.models import Gateway, MicroGateway, Stage


class ResourceURLHandler:
    @staticmethod
    def get_resource_url_tmpl(gateway_name: str, stage_name: str) -> str:
        gateway = Gateway.objects.get(name=gateway_name)
        # 微网关
        stage = Stage.objects.get(gateway=gateway, name=stage_name)
        micro_gateway: MicroGateway = stage.micro_gateway
        if micro_gateway:
            http_info = MicroGatewayHTTPInfo.from_micro_gateway_config(micro_gateway.config)
            return f"{http_info.http_url.rstrip('/')}/{{resource_path}}"

        return settings.API_RESOURCE_URL_TMPL
