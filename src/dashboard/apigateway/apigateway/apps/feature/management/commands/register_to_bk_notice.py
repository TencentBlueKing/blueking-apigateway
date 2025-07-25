# -*- coding: utf-8 -*-
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
from bk_notice_sdk.management.commands.register_application import Command as BkNoticeBaseCommand
from django.conf import settings


class Command(BkNoticeBaseCommand):
    help = "Register the bkpaas to the bk_notice service. If the bk_notice is not enabled, skip it."

    def handle(self, *args, **options):
        if not settings.ENABLE_BK_NOTICE:
            self.stdout.write(self.style.WARNING("the bk_notice is not enabled, skip register to it"))
            return

        super().handle(*args, **options)
