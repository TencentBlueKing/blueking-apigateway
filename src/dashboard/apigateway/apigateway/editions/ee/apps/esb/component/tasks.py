# -*- coding: utf-8 -*-
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
"""
同步组件到网关后台任务

因同步组件到网关耗时较长，因此，使用后台任务同步
"""

import logging

from celery import shared_task
from rest_framework.serializers import ValidationError

from apigateway.apps.esb.bkcore.models import ComponentReleaseHistory
from apigateway.apps.esb.component.helpers import get_release_lock
from apigateway.apps.esb.component.release import ComponentReleaser
from apigateway.apps.esb.component.sync import ComponentSynchronizer
from apigateway.common.exception_handler import one_line_error
from apigateway.core.models import Gateway

logger = logging.getLogger(__name__)


@shared_task(name="apigateway.apps.esb.tasks.sync_and_release_esb_components", ignore_result=True)
def sync_and_release_esb_components(gateway_id: int, release_history_id: int, username: str, lock_blocking: bool):
    logger.info("sync_and_release_esb_components task start")

    release_lock = get_release_lock()
    # 用户页面操作，采用非阻塞模式，用户并发发布，让其中一个失败
    # 项目发布时，采用阻塞模式，保证当前的组件能够发布
    if not release_lock.acquire(blocking=lock_blocking):
        logger.warning("components is releasing, please don't repeat release")
        return

    gateway = Gateway.objects.get(id=gateway_id)
    synchronizer = ComponentSynchronizer()
    releaser = ComponentReleaser(gateway, username)
    if release_history_id > 0:
        releaser.release_history = ComponentReleaseHistory.objects.get(id=release_history_id)
    else:
        releaser.release_history = None

    try:
        # sync components to gateway resources
        updated_resources = synchronizer.sync_to_resources(gateway, username=username)
        releaser.record_updated_resources(updated_resources)

        # 创建网关资源版本并发布网关
        releaser.create_resource_version()
        releaser.release()

        logger.info("sync and release components success")
    except Exception as err:
        logger.exception("failed to sync and release components")
        message = one_line_error(err) if isinstance(err, ValidationError) else str(err)
        releaser.mark_release_fail(message)

        raise
    else:
        releaser.mark_release_success()
    finally:
        release_lock.release()
