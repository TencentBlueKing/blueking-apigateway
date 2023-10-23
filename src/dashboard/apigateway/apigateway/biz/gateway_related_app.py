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
from typing import List

from django.conf import settings

from apigateway.common.error_codes import error_codes
from apigateway.core.models import GatewayRelatedApp


class GatewayRelatedAppHandler:
    @classmethod
    def add_related_app(cls, gateway_id: int, bk_app_code: str):
        """添加关联应用"""
        # 检查app能关联的网关最大数量
        cls._check_app_gateway_limit(bk_app_code)

        GatewayRelatedApp.objects.get_or_create(gateway_id=gateway_id, bk_app_code=bk_app_code)

    @staticmethod
    def _check_app_gateway_limit(bk_app_code: str):
        max_gateway_per_app = settings.API_GATEWAY_RESOURCE_LIMITS["max_gateway_count_per_app_whitelist"].get(
            bk_app_code, settings.API_GATEWAY_RESOURCE_LIMITS["max_gateway_count_per_app"]
        )
        if GatewayRelatedApp.objects.filter(bk_app_code=bk_app_code).count() >= max_gateway_per_app:
            raise error_codes.INVALID_ARGUMENT.format(
                f"The app [{bk_app_code}] exceeds the limit of the number of gateways that can be related."
                + f" The maximum limit is {max_gateway_per_app}."
            )

    @staticmethod
    def get_related_app_codes(gateway_id: int) -> List[str]:
        return list(GatewayRelatedApp.objects.filter(gateway_id=gateway_id).values_list("bk_app_code", flat=True))
