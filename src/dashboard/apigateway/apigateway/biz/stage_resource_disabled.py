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
import itertools
import operator

from apigateway.core.models import Stage, StageResourceDisabled


class StageResourceDisabledHandler:
    @staticmethod
    def filter_disabled_stages_by_gateway(gateway):
        stage_ids = Stage.objects.get_ids(gateway.id)

        queryset = StageResourceDisabled.objects.filter(stage_id__in=stage_ids)
        queryset = queryset.values("stage_id", "stage__name", "resource_id")

        disabled = sorted(queryset, key=operator.itemgetter("resource_id"))

        disabled_groups = itertools.groupby(disabled, key=operator.itemgetter("resource_id"))
        resource_disabled = {}
        for resource_id, group in disabled_groups:
            resource_disabled[resource_id] = [
                {
                    "id": stage["stage_id"],
                    "name": stage["stage__name"],
                }
                for stage in group
            ]
        return resource_disabled
