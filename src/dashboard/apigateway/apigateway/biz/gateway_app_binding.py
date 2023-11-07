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
from typing import List

from apigateway.core.models import Gateway, GatewayAppBinding


class GatewayAppBindingHandler:
    @classmethod
    def update_gateway_app_bindings(cls, gateway: Gateway, bk_app_codes: List[str]):
        """
        更新网关应用的绑定
        - 1. 如果 bk_app_codes 中应用未绑定，则新增绑定
        - 2. 如果已绑定的应用未在 bk_app_codes 中，则删除
        """
        bound_app_codes = cls.get_bound_app_codes(gateway)
        app_codes_to_add = set(bk_app_codes) - set(bound_app_codes)
        app_codes_to_delete = set(bound_app_codes) - set(bk_app_codes)

        if app_codes_to_add:
            GatewayAppBinding.objects.bulk_create(
                [GatewayAppBinding(gateway=gateway, bk_app_code=code) for code in app_codes_to_add]
            )

        if app_codes_to_delete:
            GatewayAppBinding.objects.filter(gateway=gateway, bk_app_code__in=app_codes_to_delete).delete()

    @staticmethod
    def get_bound_app_codes(gateway: Gateway) -> List[str]:
        """获取已绑定的应用"""
        return list(GatewayAppBinding.objects.filter(gateway=gateway).values_list("bk_app_code", flat=True))
