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

import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.generic import View

from healthz.utils import failed_resp, ok_resp


class CheckError(Exception):
    """检查出现错误"""


class CheckWarning(Exception):
    """检查出现警告"""


class PongView(View):
    def get(self, request):
        return HttpResponse("pong")


class HealthzView(View):
    def get(self, request):
        try:
            self._check_settings()
            self._check_db()
            self._check_third_api()
            self._check_ssl()
        except CheckError as err:
            return JsonResponse(failed_resp(message=f"Error: {err}"))
        except CheckWarning as err:
            return JsonResponse(ok_resp(message=f"Warning: some checks fail and do not affect core functions. {err}"))
        except Exception as err:
            return JsonResponse(failed_resp(message=f"Error: some unknown errors occurred, {err}"))

        return JsonResponse(ok_resp(message="OK"))

    def _check_settings(self):
        """检查 settings 配置"""
        # 不能为空
        not_allow_empty_keys = [
            "ESB_TOKEN",
            "SSL_ROOT_DIR",
            "HOST_BK_LOGIN",
            "HOST_CC_V3",
            "HOST_JOB",
        ]
        empty_keys = [key for key in not_allow_empty_keys if not getattr(settings, key, None)]
        if empty_keys:
            raise CheckError(f"These django settings should not be empty: {', '.join(empty_keys)}")

    def _check_ssl(self):
        # SSL 文件检查
        if not os.path.exists(settings.SSL_ROOT_DIR):
            raise CheckWarning(
                "The folder %s specified by SSL_ROOT_DIR in the settings configuration does not exist"
                % settings.SSL_ROOT_DIR
            )

        ssl_files_config = {
            "JOB": ["job_esb_api_client.crt", "job_esb_api_client.key"],
        }
        for system_name, ssl_files in list(ssl_files_config.items()):
            for file_name in ssl_files:
                path = os.path.join(settings.SSL_ROOT_DIR, file_name)
                if not os.path.exists(path):
                    raise CheckWarning(
                        "The ssl file %s used by component system %s does not exist" % (path, system_name)
                    )

    def _check_db(self):
        """检查 DB"""
        try:
            from esb.bkcore.models import System

            systems = System.objects.all()
            system_names = [system.name for system in systems]
        except Exception as err:
            raise CheckError("DB checks failed, {err}")

        if not system_names:
            raise CheckWarning(
                "Component system and channel data have not been initialized, "
                'please execute "python manage.py sync_system_and_channel_data" to initialize'
            )

    def _check_third_api(self):
        """检查第三方系统API"""
        self._check_cc_api()

    def _check_cc_api(self):
        try:
            from components.bk.apisv2.cc.search_business import SearchBusiness
            from esb.bkauth.models import BKUser

            result = SearchBusiness(current_user=BKUser("admin")).invoke()
            if not result["result"]:
                raise Exception(result["message"])
        except Exception as err:
            raise CheckWarning(f"System CC interface access abnormal: {err}")
