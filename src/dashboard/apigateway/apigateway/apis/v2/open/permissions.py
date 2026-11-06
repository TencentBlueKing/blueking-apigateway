# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from django.utils.translation import gettext_lazy
from rest_framework.permissions import BasePermission

from apigateway.apps.permission.constants import OAUTH2_BUILTIN_APP_CODES


class GatewayAppPermissionApplyPermission(BasePermission):
    """Only ordinary applications without an authenticated JWT user may apply."""

    message = gettext_lazy("仅允许普通应用以应用身份申请权限，不支持用户身份及 personal/public 应用。")

    def has_permission(self, request, view):
        if request.app.app_code in OAUTH2_BUILTIN_APP_CODES:
            return False

        jwt = getattr(request, "jwt", None)
        if not jwt:
            # The preceding permission requires request.app. Without JWT, only
            # SelfAppCodeAppSecretLoginMiddleware sets it after verifying our credentials.
            return True

        app = jwt.payload.get("app") or {}
        user = jwt.payload.get("user") or {}
        # request.user does not retain JWT verified, and may come from a login cookie.
        # Application-type access tokens remain supported; JWT does not identify
        # whether the application was authenticated with a secret or such a token.
        return app.get("verified") is True and user.get("verified") is False
