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
from apigateway.core.constants import PublishEventNameTypeEnum, PublishEventStatusTypeEnum
from apigateway.core.models import PublishEvent, ReleaseHistory, Stage


class PublishEventReporter:
    """
    发布事件上报
    """

    @classmethod
    def report_config_validate_doing_event(cls, publish: ReleaseHistory, stage: Stage):
        """
        dashboard 配置参数校验事件上报
        """
        PublishEvent.objects.add_event(
            gateway=publish.gateway,
            stage=stage,
            publish=publish,
            name=PublishEventNameTypeEnum.ValidateConfiguration,
            status=PublishEventStatusTypeEnum.DOING,
        )

    @classmethod
    def report_config_validate_success_event(cls, publish: ReleaseHistory, stage: Stage):
        """
        dashboard 配置参数校验成功事件上报
        """
        PublishEvent.objects.add_event(
            gateway=publish.gateway,
            stage=stage,
            publish=publish,
            name=PublishEventNameTypeEnum.ValidateConfiguration,
            status=PublishEventStatusTypeEnum.DOING,
        )

    @classmethod
    def report_config_validate_fail_event(cls, publish: ReleaseHistory, stage: Stage, msg: str):
        """
        dashboard 配置参数校验失败事件上报
        """
        PublishEvent.objects.add_event(
            gateway=publish.gateway,
            stage=stage,
            publish=publish,
            name=PublishEventNameTypeEnum.ValidateConfiguration,
            status=PublishEventStatusTypeEnum.DOING,
            detail={
                "err_msg": msg,
            },
        )

    @classmethod
    def report_create_publish_task_doing_event(cls, publish: ReleaseHistory, stage: Stage):
        """
        dashboard创建发布任务事件上报
        """
        PublishEvent.objects.add_event(
            gateway=publish.gateway,
            stage=stage,
            publish=publish,
            name=PublishEventNameTypeEnum.GenerateTask,
            status=PublishEventStatusTypeEnum.DOING,
        )

    @classmethod
    def report_create_publish_task_success_event(cls, publish: ReleaseHistory, stage: Stage):
        """
        dashboard创建发布任务成功事件上报
        """
        PublishEvent.objects.add_event(
            gateway=publish.gateway,
            stage=stage,
            publish=publish,
            name=PublishEventNameTypeEnum.GenerateTask,
            status=PublishEventStatusTypeEnum.SUCCESS,
        )

    @classmethod
    def report_distribute_configuration_doing_event(cls, publish: ReleaseHistory, stage: Stage):
        """
        dashboard下发配置执行事件上报
        """
        PublishEvent.objects.add_event(
            gateway=publish.gateway,
            stage=stage,
            publish=publish,
            name=PublishEventNameTypeEnum.DistributeConfiguration,
            status=PublishEventStatusTypeEnum.DOING,
        )

    @classmethod
    def report_distribute_configuration_success_event(cls, publish: ReleaseHistory, stage: Stage):
        """
        dashboard下发配置成功事件上报
        """
        PublishEvent.objects.add_event(
            gateway=publish.gateway,
            stage=stage,
            publish=publish,
            name=PublishEventNameTypeEnum.DistributeConfiguration,
            status=PublishEventStatusTypeEnum.SUCCESS,
        )

    @classmethod
    def report_distribute_configuration_failure_event(cls, publish: ReleaseHistory, stage: Stage, fail_msg: str):
        """
        dashboard下发配置失败事件上报
        """
        PublishEvent.objects.add_event(
            gateway=publish.gateway,
            stage=stage,
            publish=publish,
            name=PublishEventNameTypeEnum.DistributeConfiguration,
            status=PublishEventStatusTypeEnum.FAILURE,
            detail={"err_msg": fail_msg},
        )
