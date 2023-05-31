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
import time
from contextlib import contextmanager
from logging import Logger, getLogger

logger = getLogger(__name__)


class ProcedureLogger:
    """打印复杂流程的日志，并在日志中添加一些公共内容"""

    def __init__(self, name: str, logger: Logger = logger):
        self.name = name
        self.logger = logger

    @contextmanager
    def step(self, step: str, raise_exception=True, **context):
        self.logger.info("%s, step %s start", self._message_prefix, step)

        begin_time = time.time()
        try:
            yield
            self.logger.info(
                "%s, step %s finished, duration %.6fs", self._message_prefix, step, time.time() - begin_time
            )
        except Exception as e:
            if raise_exception:
                self.logger.exception("%s, step %s error", self._message_prefix, step)
                raise

            self.logger.info("%s, step %s error: %s, ignore error", self._message_prefix, step, e)

    def exception(self, message: str):
        self.logger.exception("%s, %s", self._message_prefix, message)

    def error(self, message: str):
        self.logger.error("%s, %s", self._message_prefix, message)

    def warning(self, message: str):
        self.logger.warning("%s, %s", self._message_prefix, message)

    def info(self, message: str):
        self.logger.info("%s, %s", self._message_prefix, message)

    @property
    def _message_prefix(self):
        return f"procedure {self.name}"
