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
from typing import Any

from django.conf import settings

from apigateway.common.tenant.request import gen_operation_tenant_headers
from apigateway.utils.url import url_join

from .http import http_post
from .utils import do_legacy_blueking_http_request, gen_gateway_headers


def esquery_dsl(index: str, body: Any) -> Any:
    data = {
        "indices": index,
        "body": body,
    }

    headers = gen_gateway_headers()
    headers.update(gen_operation_tenant_headers())

    gateway_name = "bk-log-search"
    if settings.EDITION == "te":
        gateway_name = "log-search"
    host = settings.BK_API_URL_TMPL.format(api_name=gateway_name)

    url = url_join(host, "/prod/esquery_dsl/")
    timeout = 30

    return do_legacy_blueking_http_request("bklog", http_post, url, data, headers, timeout)
