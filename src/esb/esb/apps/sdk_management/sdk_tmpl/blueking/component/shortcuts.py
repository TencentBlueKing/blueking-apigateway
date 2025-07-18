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

import logging

from . import conf
from .client import ComponentClient

logger = logging.getLogger("component")

__all__ = [
    "get_client_by_request",
    "get_client_by_user",
]


def get_client_by_request(request, **kwargs):
    """根据当前请求返回一个client

    :param request: 一个django request实例
    :returns: 一个初始化好的ComponentClient对象
    """
    is_authenticated = request.user.is_authenticated
    if callable(is_authenticated):
        is_authenticated = is_authenticated()
    if is_authenticated:
        bk_token = request.COOKIES.get("bk_token", "")
    else:
        bk_token = ""

    common_args = {
        "bk_token": bk_token,
    }
    common_args.update(kwargs)
    return ComponentClient(conf.APP_CODE, conf.SECRET_KEY, common_args=common_args)


def get_client_by_user(user, **kwargs):
    """根据user实例返回一个client

    :param user: User实例或者User.username数据
    :returns: 一个初始化好的ComponentClient对象
    """
    try:
        from account.models import BkUser as User
    except Exception:
        from django.contrib.auth.models import User

    try:
        if isinstance(user, User):
            username = user.username
        else:
            username = user
    except Exception:
        logger.exception("Failed to get user according to user (%s)" % user)

    common_args = {"bk_username": username}
    common_args.update(kwargs)
    return ComponentClient(conf.APP_CODE, conf.SECRET_KEY, common_args=common_args)
