#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
"""Release waiting helpers."""

import logging
import time
from datetime import datetime

from apigateway.core.constants import ReleaseHistoryStatusEnum
from apigateway.core.models import PublishEvent

logger = logging.getLogger(__name__)

DEFAULT_WAIT_RELEASE_TIMEOUT = 150


def wait_release_done(release_history_id: int, timeout: int = DEFAULT_WAIT_RELEASE_TIMEOUT) -> str:
    """轮询等待指定发布任务结束，用于滚动同步、下架等任务开始前等待上一轮发布收敛。

    调用方只需要知道发布是否已经离开 DOING 状态，不需要读取完整发布事件详情时使用。

    Args:
        release_history_id (int): 需要等待的发布历史 ID。
        timeout (int): 最长等待秒数，超过后按发布失败处理。

    Returns:
        str: 发布历史的最终状态值；超时或无最终成功事件时返回 FAILURE。
    """
    start_time = datetime.now().timestamp()
    wait_times = 0
    while True:
        now = datetime.now().timestamp()
        if now - start_time > timeout:
            logger.warning(
                "wait_release_done timeout after %ds, release_history_id=%d",
                timeout,
                release_history_id,
            )
            return ReleaseHistoryStatusEnum.FAILURE.value

        time.sleep(1 * wait_times)
        wait_times += 1

        event_map = PublishEvent.objects.get_release_history_id_to_latest_publish_event_map([release_history_id])
        latest_event = event_map.get(release_history_id)
        if not latest_event:
            continue

        status = latest_event.get_release_history_status()
        if status != ReleaseHistoryStatusEnum.DOING.value:
            return status
