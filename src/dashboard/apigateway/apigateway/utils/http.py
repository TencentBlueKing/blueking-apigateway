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
http基础方法

Rules:
1. POST/DELETE/PUT: json in
2. GET带参数，HEAD不带参数
3. 所有请求 json out，如果resp.json报错, 则是接口问题
"""
import logging

import requests

logger = logging.getLogger(__name__)


def _http_request(method, url, headers=None, data=None, timeout=None, **kwargs):
    logger.debug("request method: %s, url: %s, headers: %s, data: %s", method, url, headers, data)
    try:
        if method == "GET":
            resp = requests.get(url=url, headers=headers, params=data, timeout=timeout, **kwargs)
        elif method == "HEAD":
            resp = requests.head(url=url, headers=headers, **kwargs)
        elif method == "POST":
            resp = requests.post(url=url, headers=headers, json=data, timeout=timeout, **kwargs)
        elif method == "DELETE":
            resp = requests.delete(url=url, headers=headers, json=data, timeout=timeout, **kwargs)
        elif method == "PUT":
            resp = requests.put(url=url, headers=headers, json=data, timeout=timeout, **kwargs)
        else:
            return False, None
    except requests.exceptions.RequestException:
        logger.exception("http request error! method: %s, url: %s, data: %s", method, url, data)
        return False, None
    else:
        if resp.status_code != 200:
            content = resp.content[:100] if resp.content else ""
            error_msg = (
                "http request fail! method: %s, url: %s, data: %s, " "response_status_code: %s, response_content: %s"
            )
            logger.error(error_msg, method, url, str(data), resp.status_code, content)
            return False, None

        return True, resp.json()


def http_get(url, data, headers=None, timeout=None, **kwargs):
    return _http_request(method="GET", url=url, headers=headers, data=data, timeout=timeout, **kwargs)


def http_post(url, data, headers=None, timeout=None, **kwargs):
    return _http_request(method="POST", url=url, headers=headers, data=data, timeout=timeout, **kwargs)


def http_put(url, data, headers=None, timeout=None, **kwargs):
    return _http_request(method="PUT", url=url, headers=headers, data=data, timeout=timeout, **kwargs)


def http_delete(url, data, headers=None, timeout=None, **kwargs):
    return _http_request(method="DELETE", url=url, headers=headers, data=data, timeout=timeout, **kwargs)
