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
import logging

from celery import shared_task
from django.conf import settings

from apigateway.controller.helm.release import ReleaseHelper
from apigateway.controller.helm.values_generator import MicroGatewayValuesGenerator
from apigateway.controller.micro_gateway_config import MicroGatewayBcsInfo
from apigateway.core.constants import MicroGatewayStatusEnum
from apigateway.core.models import MicroGateway
from apigateway.utils.procedure_logger import ProcedureLogger

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def deploy_micro_gateway(micro_gateway_id, username, user_credentials):
    """部署微网关实例"""
    micro_gateway = MicroGateway.objects.get(id=micro_gateway_id)
    micro_gateway_config = micro_gateway.config
    # 不需要托管的实例，如二进制环境
    if not micro_gateway.is_managed:
        logger.info("micro gateway %s is not managed, skipped", micro_gateway_id)
        micro_gateway.status = MicroGatewayStatusEnum.UPDATED.value
        micro_gateway.save(update_fields=["status"])
        return

    logger.info("deploy micro gateway: micro_gateway_id=%s, username=%s", micro_gateway_id, username)
    # 标记部署中
    micro_gateway.status = MicroGatewayStatusEnum.INSTALLING.value
    micro_gateway.save(update_fields=["status"])

    release_helper = ReleaseHelper(user_credentials=user_credentials)
    bcs_info = MicroGatewayBcsInfo.from_micro_gateway_config(micro_gateway_config)
    values_generator = MicroGatewayValuesGenerator(micro_gateway=micro_gateway)
    procedure_logger = ProcedureLogger("edge-gateway-upgrading", logger)

    try:
        with procedure_logger.step("release-upgrading"):
            result = release_helper.ensure_release(
                # 公共仓库的 chart 需要写死
                project_id=bcs_info.project_name,
                repository=settings.BCS_PUBLIC_CHART_REPOSITORY,
                chart_name=settings.BCS_MICRO_GATEWAY_CHART_NAME,
                chart_version=bcs_info.chart_version,
                release_name=bcs_info.release_name,
                namespace=bcs_info.namespace,
                cluster_id=bcs_info.cluster_id,
                operator=username,
                values=values_generator.generate_values(),
            )

        with procedure_logger.step("config-updating"):
            bcs_info.release_revision = result.revision
            micro_gateway_config.update(bcs_info.to_micro_gateway_config())
            micro_gateway.config = micro_gateway_config
    except Exception:
        # 记录失败原因
        logger.exception("deploy micro gateway failed: micro_gateway_id=%s, username=%s", micro_gateway_id, username)
        # 标记部署失败
        micro_gateway.status = MicroGatewayStatusEnum.ABNORMAL.value
        micro_gateway.save(update_fields=["updated_time", "status"])
    else:
        # 更新成功状态
        micro_gateway.status = MicroGatewayStatusEnum.INSTALLED.value
        micro_gateway.save(update_fields=["updated_time", "status", "_config"])
