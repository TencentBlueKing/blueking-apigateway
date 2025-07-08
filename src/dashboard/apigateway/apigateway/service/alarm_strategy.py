#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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


from apigateway.apps.monitor.constants import (
    AlarmTypeEnum,
    NoticeRoleEnum,
    NoticeWayEnum,
    ResourceBackendAlarmSubTypeEnum,
)
from apigateway.apps.monitor.models import AlarmStrategy
from apigateway.common.factories import SchemaFactory
from apigateway.core.models import Gateway


def create_default_alarm_strategy(gateway: Gateway, created_by: str = ""):
    for alarm_type in [AlarmTypeEnum.RESOURCE_BACKEND]:
        for alarm_subtype in [
            ResourceBackendAlarmSubTypeEnum.STATUS_CODE_5XX,
            ResourceBackendAlarmSubTypeEnum.GATEWAY_TIMEOUT,
            ResourceBackendAlarmSubTypeEnum.BAD_GATEWAY,
        ]:
            AlarmStrategy.objects.create(
                gateway=gateway,
                name=ResourceBackendAlarmSubTypeEnum.get_choice_label(alarm_subtype),
                alarm_type=alarm_type.value,
                alarm_subtype=alarm_subtype.value,
                config={
                    "detect_config": {
                        # 单位秒，默认5分钟
                        "duration": 300,
                        "method": "gte",
                        "count": 3,
                    },
                    "converge_config": {
                        # 单位秒，默认24小时
                        "duration": 86400,
                    },
                    "notice_config": {
                        "notice_way": [NoticeWayEnum.WECHAT.value, NoticeWayEnum.IM.value],
                        "notice_role": [NoticeRoleEnum.MAINTAINER.value],
                        "notice_extra_receiver": [],
                    },
                },
                schema=SchemaFactory().get_monitor_alarm_strategy_schema(),
                enabled=True,
                created_by=created_by,
                updated_by=created_by,
            )
