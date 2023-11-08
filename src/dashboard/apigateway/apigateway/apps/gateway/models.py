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
from django.db import models

from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway


class GatewayAppBinding(TimestampedModelMixin, OperatorModelMixin):
    """
    网关绑定的蓝鲸应用
    - 仅影响 HomePage 中运维开发分数的计算
    """

    gateway = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    bk_app_code = models.CharField(max_length=32, db_index=True)

    def __str__(self):
        return f"<GatewayAppBinding: {self.bk_app_code}/{self.gateway_id}>"

    class Meta:
        db_table = "gateway_app_binding"
        unique_together = ("gateway", "bk_app_code")
