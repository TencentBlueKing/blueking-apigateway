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
import textwrap

from django.utils.translation import gettext_lazy as _

# 用户验证类型
USER_AUTH_TYPES = [
    {
        "name": "default",
        "label": _("蓝鲸用户"),
        "description": textwrap.dedent(
            """
            面向蓝鲸用户:
            - 用户通过登录蓝鲸平台，可获取蓝鲸票据 bk_token
            """
        ).strip(),
        "description_en": textwrap.dedent(
            """
            For BK User:
            - Users can log in to the BlueKing platform and get bk_token from cookies that indicates them
            """
        ).strip(),
        "login_ticket": {
            "autoload": True,
            "key_to_cookie_name": [
                ("bk_token", "bk_token"),
            ],
            "description": _("用户通过登录蓝鲸平台，可获取蓝鲸票据 bk_token"),
        },
    },
]
