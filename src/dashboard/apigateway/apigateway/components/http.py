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


import logging
import time
import uuid
from urllib.parse import urlparse

import requests
from django.conf import settings

logger = logging.getLogger("component")


def _enrich_header(headers=None):
    if not headers:
        request_id = str(uuid.uuid4()).replace("-", "")
        return {
            # only add this when the headers is not provided
            "Content-Type": "application/json",
            "X-Request-Id": request_id,
        }

    request_id = headers.get("X-Request-Id")
    if request_id:
        return headers

    request_id = str(uuid.uuid4()).replace("-", "")
    headers["X-Request-Id"] = request_id
    return headers


session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=settings.REQUESTS_POOL_CONNECTIONS, pool_maxsize=settings.REQUESTS_POOL_MAXSIZE
)
session.mount("https://", adapter)
session.mount("http://", adapter)


def _http_request(
    method, url, headers=None, data=None, timeout=None, verify=False, cert=None, cookies=None, request_session=None
):
    if request_session is None:
        request_session = session

    headers = _enrich_header(headers)
    request_id = headers.get("X-Request-Id")

    st = time.time()
    try:
        if method == "GET":
            resp = request_session.get(
                url=url, headers=headers, params=data, timeout=timeout, verify=verify, cert=cert, cookies=cookies
            )
        elif method == "HEAD":
            resp = request_session.head(url=url, headers=headers, verify=verify, cert=cert, cookies=cookies)
        elif method == "POST":
            resp = request_session.post(
                url=url, headers=headers, json=data, timeout=timeout, verify=verify, cert=cert, cookies=cookies
            )
        elif method == "DELETE":
            resp = request_session.delete(
                url=url, headers=headers, json=data, timeout=timeout, verify=verify, cert=cert, cookies=cookies
            )
        elif method == "PUT":
            resp = request_session.put(
                url=url, headers=headers, json=data, timeout=timeout, verify=verify, cert=cert, cookies=cookies
            )
        elif method == "PATCH":
            resp = request_session.patch(
                url=url, headers=headers, json=data, timeout=timeout, verify=verify, cert=cert, cookies=cookies
            )
        else:
            return False, {"error": "method not supported"}
    except requests.exceptions.RequestException as e:
        logger.exception("http request error! %s %s, data: %s, request_id: %s", method, url, data, request_id)
        return False, {"error": str(e)}
    else:
        # record for /metrics
        latency = int((time.time() - st) * 1000)

        # greater than 100ms
        if latency > 100:
            logger.warning("http slow request! method: %s, url: %s, latency: %dms", method, url, latency)

        if resp.status_code != 200:
            content = resp.content[:256] if resp.content else ""
            error_msg = (
                "http request fail! %s %s, data: %s, request_id: %s, response.status_code: %s, response.body: %s"
            )
            logger.error(error_msg, method, url, str(data), request_id, resp.status_code, content)

            return False, {
                "error": (
                    f"status_code is {resp.status_code}, not 200! "
                    f"{method} {urlparse(url).path}, request_id={request_id}, resp.body={content}"
                )
            }

        return True, resp.json()


def http_get(url, data, headers=None, verify=False, cert=None, timeout=None, cookies=None, request_session=None):
    return _http_request(
        method="GET",
        url=url,
        headers=headers,
        data=data,
        verify=verify,
        cert=cert,
        timeout=timeout,
        cookies=cookies,
        request_session=request_session,
    )


def http_post(url, data, headers=None, verify=False, cert=None, timeout=None, cookies=None, request_session=None):
    return _http_request(
        method="POST",
        url=url,
        headers=headers,
        data=data,
        timeout=timeout,
        verify=verify,
        cert=cert,
        cookies=cookies,
        request_session=request_session,
    )


def http_put(url, data, headers=None, verify=False, cert=None, timeout=None, cookies=None, request_session=None):
    return _http_request(
        method="PUT",
        url=url,
        headers=headers,
        data=data,
        timeout=timeout,
        verify=verify,
        cert=cert,
        cookies=cookies,
        request_session=request_session,
    )


def http_patch(url, data, headers=None, verify=False, cert=None, timeout=None, cookies=None, request_session=None):
    return _http_request(
        method="PATCH",
        url=url,
        headers=headers,
        data=data,
        timeout=timeout,
        verify=verify,
        cert=cert,
        cookies=cookies,
        request_session=request_session,
    )


def http_delete(url, data, headers=None, verify=False, cert=None, timeout=None, cookies=None, request_session=None):
    return _http_request(
        method="DELETE",
        url=url,
        headers=headers,
        data=data,
        timeout=timeout,
        verify=verify,
        cert=cert,
        cookies=cookies,
        request_session=request_session,
    )
