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
同步 Legacy ESB 的可复用数据到新版 ESB
此部分数据，可重复同步
"""

import logging
import re
from typing import Optional, Tuple

from celery import shared_task
from django.conf import settings

from apigateway.apps.esb.bkcore.models import AppAccount, FunctionController
from apigateway.apps.esb.constants import FunctionControllerCodeEnum
from apigateway.legacy_esb.paas2.models import AppAccount as LegacyAppAccount
from apigateway.legacy_esb.paas2.models import FunctionController as LegacyFunctionController

logger = logging.getLogger(__name__)


@shared_task(name="apigateway.legacy_esb.tasks.sync_legacy_esb_reusable_data", ignore_result=True)
def sync_legacy_esb_reusable_data():
    """"""
    synchronizer = LegacyESBSynchronizer()
    synchronizer.sync(dry_run=False)


class LegacyESBSynchronizer:
    def sync(self, dry_run: bool):
        if not getattr(settings, "BK_PAAS2_ENABLED", False):
            logger.warning("paas2 disabled, no need to sync data from it")
            return

        # self._sync_legacy_esb_app_account(dry_run)
        self._sync_legacy_function_controller(dry_run)

    def _sync_legacy_esb_app_account(self, dry_run: bool):
        legacy_app_accounts = {app.app_code: app for app in LegacyAppAccount.objects.all()}
        new_app_accounts = {app.app_code: app for app in AppAccount.objects.all()}

        for legacy_app_code, legacy_app in legacy_app_accounts.items():
            new_app = new_app_accounts.get(legacy_app_code)
            if new_app and legacy_app.app_token == new_app.app_token:
                continue

            if dry_run:
                logger.info("create or update app: %s", legacy_app_code)
                continue

            AppAccount.objects.update_or_create(
                app_code=legacy_app_code,
                defaults={
                    "app_token": legacy_app.app_token,
                    "introduction": legacy_app.introduction,
                },
            )

    def _sync_legacy_function_controller(self, dry_run: bool):
        self._sync_skip_user_auth(dry_run)
        self._sync_jwt_key(dry_run)

    def _sync_skip_user_auth(self, dry_run: bool):
        legacy_obj, new_obj, has_diff = self._add_legacy_function_controller_to_new(
            FunctionControllerCodeEnum.SKIP_USER_AUTH.value,  # type: ignore
            dry_run,
        )

        if dry_run or not (legacy_obj and new_obj and has_diff):
            return

        delimiter = re.compile(r"[^,;]+")
        wlist = set()
        wlist.update(delimiter.findall(legacy_obj.wlist))
        wlist.update(delimiter.findall(new_obj.wlist))
        new_obj.wlist = ",".join(sorted(wlist))
        new_obj.save(update_fields=["wlist"])

    def _sync_jwt_key(self, dry_run: bool):
        legacy_obj, new_obj, has_diff = self._add_legacy_function_controller_to_new(
            FunctionControllerCodeEnum.JWT_KEY.value,  # type: ignore
            dry_run,
        )

        if dry_run or not (legacy_obj and new_obj and has_diff):
            return

        new_obj.wlist = legacy_obj.wlist
        new_obj.save(update_fields=["wlist"])

    def _add_legacy_function_controller_to_new(
        self,
        func_code: str,
        dry_run: bool,
    ) -> Tuple[Optional[LegacyFunctionController], Optional[FunctionController], bool]:
        legacy_obj = LegacyFunctionController.objects.filter(func_code=func_code).first()
        if not legacy_obj:
            return None, None, False

        if dry_run:
            new_obj = FunctionController.objects.filter(func_code=legacy_obj.func_code).first()
            if not (new_obj and legacy_obj.wlist == new_obj.wlist):
                logger.info("create or update function_controller: %s", legacy_obj.func_code)
                return legacy_obj, new_obj, True

        new_obj, created = FunctionController.objects.get_or_create(
            func_code=legacy_obj.func_code,
            defaults={
                "func_name": legacy_obj.func_name,
                "func_desc": legacy_obj.func_desc,
                "switch_status": legacy_obj.switch_status,
                "wlist": legacy_obj.wlist,
            },
        )
        if created or legacy_obj.wlist == new_obj.wlist:
            return legacy_obj, new_obj, False

        return legacy_obj, new_obj, True
