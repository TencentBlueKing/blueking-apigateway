#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the MIT License (the "License"); you may not use this file except
#  in compliance with the License. You may obtain a copy of the License at
#  #
#      http://opensource.org/licenses/MIT
#  #
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
#  either express or implied. See the License for the specific language governing permissions and
#  limitations under the License.
#  #
#  We undertake not to change the open source license (MIT license) applicable
#  to the current version of the project delivered to anyone in the future.
#  #
from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway, Stage


class ProgrammableGatewayDeployHistory(TimestampedModelMixin, OperatorModelMixin):
    """
    Deploy Code gateway History
    """

    gateway = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    branch = models.CharField(max_length=128, blank=True, null=True)
    version = models.CharField(max_length=128, default="", db_index=True, help_text=_("符合 semver 规范"))
    commit_id = models.CharField(max_length=128, blank=True, null=True)
    deploy_id = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f"<Deploy: {self.gateway}/{self.stage}/{self.version}>"

    class Meta:
        verbose_name = "ProgrammableGatewayHistory"
        verbose_name_plural = "ProgrammableGatewayHistory"
        db_table = "programmable_gateway_deploy_history"
