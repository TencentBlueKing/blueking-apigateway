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
from typing import Tuple

from cachetools import TTLCache, cached
from django.conf import settings
from iam import IAM
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed as RESTAuthenticationFailed

from apigateway.apis.iam.exceptions import AuthenticationFailed
from apigateway.common.constants import CACHE_MAXSIZE, CACHE_TIME_5_MINUTES


class IAMBasicAuthentication(BasicAuthentication):
    """自定义认证逻辑, 对权限中心请求认证"""

    def authenticate(self, request):
        try:
            result = super().authenticate(request)
            if result is None:
                raise AuthenticationFailed("basic auth failed")
        except RESTAuthenticationFailed as err:
            raise AuthenticationFailed(str(err))

        return result

    def authenticate_credentials(self, userid: str, password: str, request=None):
        if userid != "bk_iam":
            raise AuthenticationFailed("username is not bk_iam")

        ok, msg, token = self._get_iam_token()
        if not ok:
            raise AuthenticationFailed(f"get system token failed: {msg}")

        if password != token:
            raise AuthenticationFailed("password in basic auth not equals to system token")

        return ({"username": userid, "password": password}, None)

    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TIME_5_MINUTES))
    def _get_iam_token(self) -> Tuple[bool, str, str]:
        iam_client = IAM(
            app_code=settings.BK_APP_CODE,
            app_secret=settings.BK_APP_SECRET,
            bk_apigateway_url=settings.BK_IAM_APIGATEWAY_URL,
        )
        return iam_client.get_token(settings.BK_IAM_SYSTEM_ID)
