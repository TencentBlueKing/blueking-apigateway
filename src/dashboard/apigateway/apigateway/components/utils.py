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
import json
from typing import Dict

from django.conf import settings
from django.utils.translation import get_language


def inject_accept_language(request):
    language = get_language()
    if language:
        request.headers["Accept-Language"] = language


def gen_gateway_headers() -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "X-Bkapi-Authorization": json.dumps(
            {
                "bk_app_code": settings.BK_APP_CODE,
                "bk_app_secret": settings.BK_APP_SECRET,
            }
        ),
    }
    language = get_language()
    if language:
        headers["Accept-Language"] = language

    return headers
