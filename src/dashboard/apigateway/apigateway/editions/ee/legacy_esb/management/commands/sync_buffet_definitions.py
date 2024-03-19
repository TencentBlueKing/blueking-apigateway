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
"""迁移 PaaS2/ESB 自助接入组件至 API Gateway"""

import logging
import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apigateway.legacy_esb import models as legacy_models
from apigateway.legacy_esb.management.commands import pre_check_buffet_data

logger = logging.getLogger(__name__)

_BUFFET_API_NAME = "bk-esb-buffet"
_DASHBOARD_INNER_URL = os.environ.get("DASHBOARD_INNER_URL", "http://apigw-dashboard.service.consul:6000")
_APIGW_DEFINITIONS_DIR = os.path.join(settings.BASE_DIR, "data/apigw-definitions")


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not legacy_models.ESBBuffetComponent.objects.all():
            logger.info("不存在自助接入的组件，跳过自助接入组件的迁移步骤")
            return

        # 预检数据，如果数据不符合预期，将不会继续同步数据
        pre_check_buffet_data.Command().handle()

        call_command(
            "export_buffet_to_resources",
            f"--file-path={_APIGW_DEFINITIONS_DIR}/bk-esb-buffet-resources.yaml",
        )
        self._sync_buffet_definitions()

    def _sync_buffet_definitions(self):
        call_command(
            "sync_apigw_config",
            f"--api-name={_BUFFET_API_NAME}",
            f"--host={_DASHBOARD_INNER_URL}/backend",
            f"--file={_APIGW_DEFINITIONS_DIR}/bk-esb-buffet-definition.yaml",
        )
        call_command(
            "sync_apigw_stage",
            f"--api-name={_BUFFET_API_NAME}",
            f"--host={_DASHBOARD_INNER_URL}/backend",
            f"--file={_APIGW_DEFINITIONS_DIR}/bk-esb-buffet-definition.yaml",
        )
        call_command(
            "sync_apigw_resources",
            f"--api-name={_BUFFET_API_NAME}",
            f"--host={_DASHBOARD_INNER_URL}/backend",
            f"--file={_APIGW_DEFINITIONS_DIR}/bk-esb-buffet-resources.yaml",
        )
        call_command(
            "create_version_and_release_apigw",
            f"--api-name={_BUFFET_API_NAME}",
            f"--host={_DASHBOARD_INNER_URL}/backend",
            f"--file={_APIGW_DEFINITIONS_DIR}/bk-esb-buffet-definition.yaml",
        )
