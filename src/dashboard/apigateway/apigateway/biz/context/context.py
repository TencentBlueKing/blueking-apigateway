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

from collections import defaultdict

from apigateway.core.models import Context
from apigateway.schema.models import Schema


class ContextHandler:
    @staticmethod
    def filter_id_type_snapshot_map(scope_type, scope_ids):
        """
        获取 id=>type=>snapshot 的数据，如
        {
            1: {
                "resource_auth": {
                    "id": 123,
                    ...
                }
            }
        }
        """

        schemas = Schema.objects.filter_id_snapshot_map()
        id_type_snapshot_map = defaultdict(dict)
        queryset = Context.objects.filter(scope_type=scope_type, scope_id__in=scope_ids)
        for c in queryset:
            id_type_snapshot_map[c.scope_id][c.type] = c.snapshot(
                as_dict=True,
                schemas=schemas,
            )
        return id_type_snapshot_map
