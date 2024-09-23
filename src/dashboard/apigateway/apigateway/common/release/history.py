#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from datetime import datetime

from apigateway.core.constants import (
    EVENT_FAIL_INTERVAL_TIME,
    PublishEventStatusEnum,
    ReleaseHistoryStatusEnum,
)
from apigateway.core.models import PublishEvent


def get_status(last_event: PublishEvent):
    """通过 end event 来返回 release_history 状态"""
    # 如果状态是 Doing 并且该状态已经过去了 10min，这种也认失败
    now = datetime.now().timestamp()
    if last_event.status == PublishEventStatusEnum.DOING.value and now - last_event.created_time.timestamp() > 600:
        return ReleaseHistoryStatusEnum.FAILURE.value

    # 如果是成功但不是最后一个节点并且该状态已经过去了 10min，这种也认失败
    if (
        last_event.status == PublishEventStatusEnum.SUCCESS.value and not last_event.is_last
    ) and now - last_event.created_time.timestamp() > EVENT_FAIL_INTERVAL_TIME:
        return ReleaseHistoryStatusEnum.FAILURE.value

    # 如果还在执行中
    # if ReleaseHandler.is_running(last_event):
    if last_event.is_running:
        return ReleaseHistoryStatusEnum.DOING.value

    # 如已经结束
    if last_event.status == PublishEventStatusEnum.SUCCESS.value:
        return ReleaseHistoryStatusEnum.SUCCESS.value

    if last_event.status == PublishEventStatusEnum.FAILURE.value:
        return ReleaseHistoryStatusEnum.FAILURE.value

    return ReleaseHistoryStatusEnum.DOING.value
