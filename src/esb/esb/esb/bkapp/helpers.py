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
from typing import List, Optional, Tuple

from cachetools import TTLCache, cached
from django.conf import settings

from esb.bkcore.models import AppAccount
from esb.paas2.models import App


class AppSecureInfo:
    """
    Helper for AppSecureInfo
    """

    @classmethod
    @cached(cache=TTLCache(maxsize=2000, ttl=300))
    def get_by_app_code(cls, app_code: str) -> Optional[dict]:
        secure_key_list = []

        # get secret from paas
        if settings.BK_PAAS2_ENABLED:
            app = App.objects.filter(code=app_code).first()
            if app:
                secure_key_list.append(app.auth_token)

        # get secret from esb
        app = AppAccount.objects.filter(app_code=app_code).first()
        if app:
            secure_key_list.append(app.app_token)

        return {"app_code": app_code, "secure_key_list": secure_key_list} if secure_key_list else None


class BKAuthHelper:
    @classmethod
    @cached(
        cache=TTLCache(
            maxsize=settings.LIST_APP_SECRETS_CACHE_MAXSIZE,
            ttl=settings.LIST_APP_SECRETS_CACHE_TTL,
        )
    )
    def list_app_secrets(cls, app_code: str) -> Tuple[List[str], str]:
        # TODO: 待 bkauth 上线后删除此部分代码
        if not settings.BK_AUTH_ENABLED:
            app_info = AppSecureInfo.get_by_app_code(app_code)
            if not app_info:
                return (
                    [],
                    f"Invalid APP Code [bk_app_code={app_code}], please confirm if the APP Code has been registered",
                )
            return app_info["secure_key_list"], "ok"

        from components.bk.apisv2.bk_auth.list_app_secrets import ListAppSecrets

        result = ListAppSecrets().invoke(kwargs={"target_app_code": app_code})
        if not result["result"]:
            # 请求 bkauth 成功，即缓存数据，因此，此处不要抛出异常
            return [], f"bkauth: {result['message']}"

        app_secrets = [item["bk_app_secret"] for item in result["data"]]
        if not app_secrets:
            return [], f"Invalid APP Code [bk_app_code={app_code}], please confirm if the APP Code has been registered"

        return app_secrets, "ok"

    @classmethod
    @cached(
        cache=TTLCache(
            maxsize=settings.VERIFY_APP_SECRET_RESULT_CACHE_MAXSIZE,
            ttl=settings.VERIFY_APP_SECRET_RESULT_CACHE_TTL,
        )
    )
    def verify_app_secret(cls, app_code: str, app_secret: str) -> Tuple[bool, str]:
        # TODO: 待 bkauth 上线后删除此部分代码
        if not settings.BK_AUTH_ENABLED:
            app_info = AppSecureInfo.get_by_app_code(app_code)
            if not app_info:
                return (
                    False,
                    f"Invalid APP Code [bk_app_code={app_code}], please confirm if the APP Code has been registered",
                )
            verified = app_secret in app_info["secure_key_list"]
            if verified:
                message = "ok"
            else:
                message = (
                    "APP Secret verification failed, "
                    f"pelase confirm if the APP Secret and APP Code [bk_app_code={app_code}] match"
                )
            return verified, message

        from components.bk.apisv2.bk_auth.verify_app_secret import VerifyAppSecret

        result = VerifyAppSecret().invoke(kwargs={"target_app_code": app_code, "target_app_secret": app_secret})
        if not result["result"]:
            # 请求 bkauth 成功，即缓存数据，因此，此处不要抛出异常
            return False, f"bkauth: {result['message']}"

        return result["data"]["is_match"], result["message"]
