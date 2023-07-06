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
from apigateway.core.constants import PublishEventEnum, PublishEventStatusEnum
from apigateway.core.models import PublishEvent


class PublishEventReporter:
    """
    发布事件上报
    """

    @classmethod
    def report_doing_create_publish_task_event(cls, gateway_id, stage_id, publish_id):
        """
        dashboard创建发布任务事件上报
        """
        PublishEvent.objects.add_event(
            gateway_id=gateway_id,
            stage_id=stage_id,
            publish_id=publish_id,
            name=PublishEventEnum.GenerateTask,
            status=PublishEventStatusEnum.DOING,
        )

    @classmethod
    def report_success_create_publish_task_event(cls, gateway_id, stage_id, publish_id):
        """
        dashboard创建发布任务成功事件上报
        """
        PublishEvent.objects.add_event(
            gateway_id=gateway_id,
            stage_id=stage_id,
            publish_id=publish_id,
            name=PublishEventEnum.GenerateTask,
            status=PublishEventStatusEnum.SUCCESS,
        )

    @classmethod
    def report_doing_distribute_configuration_event(cls, gateway_id, stage_id, publish_id):
        """
        dashboard下发配置执行事件上报
        """
        PublishEvent.objects.add_event(
            gateway_id=gateway_id,
            stage_id=stage_id,
            publish_id=publish_id,
            name=PublishEventEnum.DistributeConfiguration,
            status=PublishEventStatusEnum.DOING,
        )

    @classmethod
    def report_success_distribute_configuration_event(cls, gateway_id, stage_id, publish_id):
        """
        dashboard下发配置成功事件上报
        """
        PublishEvent.objects.add_event(
            gateway_id=gateway_id,
            stage_id=stage_id,
            publish_id=publish_id,
            name=PublishEventEnum.DistributeConfiguration,
            status=PublishEventStatusEnum.SUCCESS,
        )

    @classmethod
    def report_fail_distribute_configuration_event(cls, gateway_id, stage_id, publish_id):
        """
        dashboard下发配置失败事件上报
        """
        PublishEvent.objects.add_event(
            gateway_id=gateway_id,
            stage_id=stage_id,
            publish_id=publish_id,
            name=PublishEventEnum.DistributeConfiguration,
            status=PublishEventStatusEnum.FAILURE,
        )
