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
import uuid
from typing import Optional

from blue_krill.async_utils.django_utils import delay_on_commit
from celery import shared_task
from django.conf import settings

from apigateway.controller.distributor.combine import CombineDistributor
from apigateway.controller.procedure_logger.release_logger import ReleaseProcedureLogger
from apigateway.core.constants import APIHostingTypeEnum, APIStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, MicroGateway, Release, Stage
from apigateway.utils.redis_utils import get_default_redis_client, get_redis_key

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def rolling_update_release(gateway_id, publish_id: Optional[int] = None):
    """滚动同步微网关配置，不会生成新的版本"""
    # 剔除非微网关托管的网关
    logger.info("rolling_update_release[gateway_id=%d] begin", gateway_id)
    gateway = Gateway.objects.get(pk=gateway_id)
    if gateway.hosting_type != APIHostingTypeEnum.MICRO.value:
        logger.info("rolling_update_release: gateway(id=%d) not exist or is not a micro-gateway, skip", gateway_id)
        return False

    if gateway.status != APIStatusEnum.ACTIVE.value:
        logger.info("rolling_update_release: gateway(id=%d) is not active, skip", gateway_id)
        return False

    shared_gateway = MicroGateway.objects.get_default_shared_gateway()
    distributor = CombineDistributor()

    release_task_id = str(uuid.uuid4())

    has_failure = False
    for release in Release.objects.filter(api_id=gateway.id).prefetch_related("stage"):
        procedure_logger = ReleaseProcedureLogger(
            "rolling_update_release",
            logger=logger,
            gateway=release.api,
            stage=release.stage,
            micro_gateway=shared_gateway,
            release_task_id=release_task_id,
            publish_id=publish_id,
        )

        stage = release.stage
        if not stage:
            procedure_logger.warning(f"release(id={release.pk}) has not stage, ignored")
            continue
        elif stage.status != StageStatusEnum.ACTIVE.value:
            procedure_logger.warning("stage is not active, ignored")
            continue

        procedure_logger.info("distribute begin")
        if not distributor.distribute(
            release,
            micro_gateway=shared_gateway,
            release_task_id=release_task_id,
            publish_id=publish_id,
        ):
            procedure_logger.info("distribute failed")
            has_failure = True
        else:
            procedure_logger.info("distribute succeeded")

    return not has_failure


@shared_task(ignore_result=True)
def release_updated_check():
    """检查微网关是否需要同步"""
    client = get_default_redis_client()
    key = get_redis_key(settings.APIGW_REVERSION_UPDATE_SET_KEY)

    pipe = client.pipeline()
    pipe.smembers(key)
    pipe.delete(key)
    gateway_ids, _ = pipe.execute()

    if not gateway_ids:
        return False

    matched_gateway_ids = Gateway.objects.query_micro_and_active_ids(map(int, gateway_ids))
    logger.info(
        "release_check, gateway received count=%d, release count=%d", len(gateway_ids), len(matched_gateway_ids)
    )

    if not matched_gateway_ids:
        return False

    for gateway_id in matched_gateway_ids:
        logger.info("release_check apply rolling_update_release task for gateway(id=%d)", gateway_id)
        delay_on_commit(rolling_update_release, gateway_id)

    return True


@shared_task(ignore_result=True)
def revoke_release_by_stage(stage_id):
    """删除环境的已发布的资源"""
    stage = Stage.objects.get(pk=stage_id)
    shared_gateway = MicroGateway.objects.get_default_shared_gateway()

    procedure_logger = ReleaseProcedureLogger(
        "revoke_release",
        logger=logger,
        gateway=stage.api,
        stage=stage,
        micro_gateway=shared_gateway,
    )

    distributor = CombineDistributor()
    procedure_logger.info("revoke begin")
    distributor.revoke(stage, shared_gateway, procedure_logger.release_task_id)


@shared_task(ignore_result=True)
def revoke_release(gateway_id):
    """删除网关的已发布的资源"""

    gateway = Gateway.objects.get(pk=gateway_id)
    if not gateway.is_micro_gateway:
        logger.warning("revoke_release gateway=%s(%d) is not a micro-gateway, ignored", gateway.name, gateway.id)
        return

    for stage_id in gateway.stage_set.all().values_list("pk", flat=True):
        revoke_release_by_stage.delay(stage_id=stage_id)
