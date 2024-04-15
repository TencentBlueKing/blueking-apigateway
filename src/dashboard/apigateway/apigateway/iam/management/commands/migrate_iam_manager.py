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
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from apigateway.biz.iam import IAMHandler
from apigateway.core.models import Gateway
from apigateway.iam.models import IAMGradeManager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """迁移网关权限数据到iam分级管理员"""

    def handle(self, *args, **options):
        if not settings.USE_BK_IAM_PERMISSION:
            return

        # 遍历gateway, 迁移proxy配置
        qs = Gateway.objects.all().order_by("id")

        logger.info("start migrate iam manager, all gateway count %s", qs.count())

        iam_handler = IAMHandler()

        paginator = Paginator(qs, 100)
        for i in paginator.page_range:
            for gateway in paginator.page(i):
                if not IAMGradeManager.objects.filter(gateway=gateway).exists():
                    iam_handler.register_grade_manager_and_builtin_user_groups(gateway)

        logger.info("finish migrate iam manager")
