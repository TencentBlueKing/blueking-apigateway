#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) 2025 Tencent. All rights reserved.
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
from typing import ClassVar

from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.apps.programmable_gateway.managers import ProgrammableGatewayDeployHistoryManager
from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.constants import PublishSourceEnum
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
    deploy_id = models.CharField(max_length=128, blank=True, db_index=True, null=True)
    # 发布来源
    source = models.CharField(
        max_length=64,
        choices=[
            # 编程网关部署只有三种发布来源：版本发布、环境下架、网关停用
            (
                PublishSourceEnum.GATEWAY_DISABLE.value,
                PublishSourceEnum.get_choice_label(PublishSourceEnum.GATEWAY_DISABLE),
            ),
            (
                PublishSourceEnum.VERSION_PUBLISH.value,
                PublishSourceEnum.get_choice_label(PublishSourceEnum.VERSION_PUBLISH.value),
            ),
            (
                PublishSourceEnum.STAGE_DISABLE.value,
                PublishSourceEnum.get_choice_label(PublishSourceEnum.STAGE_DISABLE),
            ),
        ],
        default=PublishSourceEnum.VERSION_PUBLISH.value,
    )
    # publish_id -> ReleaseHistory.id
    publish_id = models.IntegerField(blank=True, null=True)
    objects: ClassVar[ProgrammableGatewayDeployHistoryManager] = ProgrammableGatewayDeployHistoryManager()

    def __str__(self):
        return f"<Deploy: {self.gateway}/{self.stage}/{self.version}>"

    class Meta:
        verbose_name = "ProgrammableGatewayHistory"
        verbose_name_plural = "ProgrammableGatewayHistory"
        db_table = "programmable_gateway_deploy_history"
