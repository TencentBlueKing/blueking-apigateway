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
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from apigateway.core.models import MicroGateway, Release


class BaseDistributor(ABC):
    @abstractmethod
    def distribute(
        self,
        release: Release,
        micro_gateway: MicroGateway,
        release_task_id: Optional[str] = None,
        publish_id: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """发布到微网关"""
        raise NotImplementedError()

    @abstractmethod
    def revoke(
        self,
        release: Release,
        micro_gateway: MicroGateway,
        release_task_id: Optional[str] = None,
        publish_id: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """撤销微网关已发布内容"""
        raise NotImplementedError()
