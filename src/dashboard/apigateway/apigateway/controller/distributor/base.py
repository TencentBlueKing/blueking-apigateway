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
from typing import Optional

from apigateway.core.models import MicroGateway, Release, Stage


class BaseDistributor:
    def distribute(
        self,
        release: Release,
        micro_gateway: MicroGateway,
        release_task_id: Optional[str] = None,
        publish_id: Optional[int] = None,
    ) -> bool:
        """发布到微网关"""
        raise NotImplementedError()

    def revoke(
        self,
        stage: Stage,
        micro_gateway: MicroGateway,
        release_task_id: Optional[str] = None,
        release_history_id: Optional[int] = None,
    ) -> bool:
        """撤销微网关已发布内容"""
        raise NotImplementedError()
