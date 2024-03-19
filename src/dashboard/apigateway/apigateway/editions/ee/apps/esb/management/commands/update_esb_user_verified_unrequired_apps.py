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
更新 ESB 免用户认证应用白名单
- 此部分数据，可重复更新
"""

import logging
import re
from typing import List

from django.core.management.base import BaseCommand

from apigateway.apps.esb.bkcore.models import FunctionController
from apigateway.apps.esb.constants import FunctionControllerCodeEnum

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("bk_app_codes", nargs="*", help="user verification excepted apps")

    def handle(self, bk_app_codes: List[str], *args, **options):
        self._update_esb_user_verified_unrequired_apps(bk_app_codes)

    def _update_esb_user_verified_unrequired_apps(self, bk_app_codes):
        if not bk_app_codes:
            return

        obj, _ = FunctionController.objects.get_or_create(
            func_code=FunctionControllerCodeEnum.SKIP_USER_AUTH.value,
            defaults={
                "func_name": FunctionControllerCodeEnum.get_choice_label(FunctionControllerCodeEnum.SKIP_USER_AUTH),
                "func_desc": "",
                "switch_status": True,
                "wlist": "",
            },
        )

        wlist = set()
        wlist.update(re.findall(r"[^,;]+", obj.wlist))
        wlist.update(bk_app_codes)

        obj.wlist = ",".join(sorted(wlist))
        obj.save(update_fields=["wlist"])
