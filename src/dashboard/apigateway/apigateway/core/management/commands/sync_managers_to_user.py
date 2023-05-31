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
将 settings 中的 APIGW_MANAGERS 同步到 django user 表，并将其设置为超级用户
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apigateway.utils.string import random_string


class Command(BaseCommand):
    def handle(self, **options):
        UserModel = get_user_model()
        for username in getattr(settings, "APIGW_MANAGERS", None) or []:
            if not username:
                continue

            user, created = UserModel.objects.get_or_create(
                username=username,
                defaults={
                    "is_active": True,
                    "is_staff": True,
                    "is_superuser": True,
                },
            )

            if created:
                user.set_password(random_string())
                user.save()

            if not (created or user.is_superuser):
                user.is_active = True
                user.is_staff = True
                user.is_superuser = True
                user.save()
