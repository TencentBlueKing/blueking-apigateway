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
import uuid
from logging import Logger
from typing import Optional

from apigateway.core.models import Gateway, MicroGateway, Stage
from apigateway.utils.procedure_logger import ProcedureLogger


class ReleaseProcedureLogger(ProcedureLogger):
    """微网关发布过程日志记录器，便于记录发布的网关，环境，微网关实例等信息"""

    def __init__(
        self,
        name: str,
        logger: Logger,
        gateway: Gateway,
        stage: Optional[Stage] = None,
        micro_gateway: Optional[MicroGateway] = None,
        release_task_id: Optional[str] = None,
        publish_id: Optional[int] = None,
    ):
        """
        :param release_task_id: 发布任务ID，触发发布任务时，可以设置一个 uuid 字符串，其将会打印到日志中，便于过滤日志
        """
        super().__init__(name, logger)
        self._gateway = gateway
        self._stage = stage
        self._micro_gateway = micro_gateway
        self.release_task_id = release_task_id or str(uuid.uuid4())
        self._publish_id = publish_id

    @property
    def _message_prefix(self):
        parts = []

        parts.append(f"gateway={self._gateway.name}({self._gateway.id})")

        if self._stage:
            parts.append(f"stage={self._stage.name}")

        if self._micro_gateway:
            parts.append(f"micro_gateway={self._micro_gateway.pk}")
        if self._publish_id:
            parts.append(f"publish_id={self._publish_id}")
        parts.append(f"release_task_id={self.release_task_id}")

        return f"procedure {self.name}: {', '.join(parts)}"
