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
from apigateway.core.models import Gateway, Resource


class APILabel(TimestampedModelMixin, OperatorModelMixin):
    """
    Gateway labels, a label set
    """

    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    name = models.CharField(max_length=32)

    class Meta:
        unique_together = ("gateway", "name")
        db_table = "label_api"

    def __str__(self):
        return f"<GatewayLabel: {self.id}/{self.name}>"


class ResourceLabel(TimestampedModelMixin):
    """
    Resource label
    resource - api_label
    """

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    api_label = models.ForeignKey(APILabel, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("resource", "api_label")
        db_table = "label_resource"
