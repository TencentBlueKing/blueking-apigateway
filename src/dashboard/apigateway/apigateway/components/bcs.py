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
from bkapi.bcs_api_gateway.client import Client
from bkapi_client_core.base import Operation
from django.conf import settings


class BcsApiGatewayClient(Client):
    def __init__(self, token=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        self.session.path_params["version"] = "v4"

        self.api.register(
            "list_cluster_namespaces",
            Operation(method="GET", path="/clusters/{cluster_id}/api/v1/namespaces/"),
        )


def get_bcs_api_gateway_client() -> BcsApiGatewayClient:
    client = BcsApiGatewayClient(endpoint=settings.BK_API_URL_TMPL)
    client.update_bkapi_authorization(bk_app_code=settings.BK_APP_CODE, bk_app_secret=settings.BK_APP_SECRET)
    return client


def get_bcs_api_gateway_admin_client() -> BcsApiGatewayClient:
    client = BcsApiGatewayClient(endpoint=settings.BK_API_URL_TMPL, token=settings.BCS_API_GATEWAY_TOKEN)
    client.update_bkapi_authorization(bk_app_code=settings.BK_APP_CODE, bk_app_secret=settings.BK_APP_SECRET)
    return client
