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

from apigateway.core.constants import PublishEventNameTypeEnum, PublishEventStatusTypeEnum, PublishSourceEnum
from apigateway.core.models import PublishEvent, ReleaseHistory


class PublishEventReporter:
    """
    发布事件上报
    """

    @classmethod
    def _report_event(
        cls,
        publish: Optional[ReleaseHistory],
        name: PublishEventNameTypeEnum,
        status: PublishEventStatusTypeEnum,
        detail: Optional[dict] = None,
    ):
        if not publish:
            return None

        if publish.source == PublishSourceEnum.CLI_SYNC.value:
            return None

        return PublishEvent.objects.create(
            gateway=publish.gateway,
            stage=publish.stage,
            step=PublishEventNameTypeEnum.get_event_step(name.value),
            publish=publish,
            name=name.value,
            detail=detail,
            status=status.value,
        )

    @classmethod
    def report_config_validate_doing(cls, publish: Optional[ReleaseHistory]):
        """
        dashboard 配置参数校验事件上报
        """
        name = PublishEventNameTypeEnum.VALIDATE_CONFIGURATION
        status = PublishEventStatusTypeEnum.DOING
        detail = None

        cls._report_event(publish, name, status, detail)

    @classmethod
    def report_config_validate_success(cls, publish: Optional[ReleaseHistory]):
        """
        dashboard 配置参数校验成功事件上报
        """
        name = PublishEventNameTypeEnum.VALIDATE_CONFIGURATION
        status = PublishEventStatusTypeEnum.SUCCESS
        detail = None

        cls._report_event(publish, name, status, detail)

    @classmethod
    def report_config_validate_failure(cls, publish: Optional[ReleaseHistory], msg: str):
        """
        dashboard 配置参数校验失败事件上报
        """
        name = PublishEventNameTypeEnum.VALIDATE_CONFIGURATION
        status = PublishEventStatusTypeEnum.FAILURE
        detail = {
            "err_msg": msg,
        }

        cls._report_event(publish, name, status, detail)

    @classmethod
    def report_create_publish_task_doing(cls, publish: Optional[ReleaseHistory]):
        """
        dashboard 创建发布任务事件上报
        """
        name = PublishEventNameTypeEnum.GENERATE_TASK
        status = PublishEventStatusTypeEnum.DOING
        detail = None

        cls._report_event(publish, name, status, detail)

    @classmethod
    def report_create_publish_task_success(cls, publish: Optional[ReleaseHistory]):
        """
        dashboard 创建发布任务成功事件上报
        """
        name = PublishEventNameTypeEnum.GENERATE_TASK
        status = PublishEventStatusTypeEnum.SUCCESS
        detail = None

        cls._report_event(publish, name, status, detail)

    @classmethod
    def report_distribute_config_doing(cls, publish: Optional[ReleaseHistory]):
        """
        dashboard 下发配置执行事件上报
        """
        name = PublishEventNameTypeEnum.DISTRIBUTE_CONFIGURATION
        status = PublishEventStatusTypeEnum.DOING
        detail = None

        cls._report_event(publish, name, status, detail)

    @classmethod
    def report_distribute_config_success(cls, publish: Optional[ReleaseHistory]):
        """
        dashboard 下发配置成功事件上报
        """
        name = PublishEventNameTypeEnum.DISTRIBUTE_CONFIGURATION
        status = PublishEventStatusTypeEnum.SUCCESS
        detail = None

        cls._report_event(publish, name, status, detail)

    @classmethod
    def report_distribute_config_failure(cls, publish: Optional[ReleaseHistory], msg: str):
        """
        dashboard 下发配置失败事件上报
        """
        name = PublishEventNameTypeEnum.DISTRIBUTE_CONFIGURATION
        status = PublishEventStatusTypeEnum.FAILURE
        detail = {"err_msg": msg}

        cls._report_event(publish, name, status, detail)
