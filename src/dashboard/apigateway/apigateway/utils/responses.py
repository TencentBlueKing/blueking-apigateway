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

from typing import Any, Dict, List, Union

from django.http import FileResponse, HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.renderers import JSONRenderer


class FailJsonResponse(JsonResponse):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        details: Union[List[Dict[str, Any]], None] = None,
        data: Union[Dict, List, None] = None,
    ):
        body = {
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
                "data": data or {},
            }
        }

        super(FailJsonResponse, self).__init__(body, status=status)


def OKJsonResponse(status: int = status.HTTP_200_OK, data: Union[Dict, List, None] = None):
    if status == 204:
        return HttpResponse(status=204)

    body = {"data": data}
    return JsonResponse(body, status=status)


class V1FailJsonResponse(JsonResponse):
    """for legacy open api only!!!"""

    def __init__(self, message, **kwargs):
        data = {}
        if kwargs:
            data.update(kwargs)

        data.setdefault("code", 40000)
        data.setdefault("data", None)

        # high priority
        data.update(
            {
                "result": False,
                "message": message,
            }
        )

        super(V1FailJsonResponse, self).__init__(data, status=status.HTTP_400_BAD_REQUEST)


class V1OKJsonResponse(JsonResponse):
    """for legacy open api only!!!"""

    def __init__(self, message="OK", **kwargs):
        data = {}
        if kwargs:
            data.update(kwargs)

        data.setdefault("code", 0)
        data.setdefault("data", None)

        # high priority
        data.update(
            {
                "result": True,
                "message": message,
            }
        )

        super(V1OKJsonResponse, self).__init__(data)


class DownloadableResponse(FileResponse):
    def __init__(self, streaming_content=(), filename=None):
        super().__init__(streaming_content)

        self["Content-Type"] = "application/octet-stream"
        self["Content-Disposition"] = f'attachment;filename="{filename}"'

        # support CORS
        self["Access-Control-Allow-Origin"] = "*"
        self["Access-Control-Allow-Headers"] = "Content-Type,Content-Disposition"
        self["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        self["Access-Control-Expose-Headers"] = "Content-Type,Content-Disposition"


class ResponseRender(JSONRenderer):
    """将 DRF 返回的结构进行标准化转换，兼容 error handler 处理结果"""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context["response"]
        if response.status_code == status.HTTP_204_NO_CONTENT:
            # status 204 no-content，如果设置了 content-length，可能导致客户端卡死，
            # 并且，现在采用的接口规范，所有请求都返回一个 json 格式消息: {"code": 0, "message": ""}
            response.status_code = status.HTTP_200_OK

        result = {
            "message": "",
            "data": None,
        }

        if response.status_code < 400:
            # ok response from drf or django views

            result["code"] = 0
            result["result"] = True
            result["data"] = data

        elif "code" in data:
            # custom error handler wrapped response
            result = data

        else:
            # failure response
            result["code"] = response.status_code * 100
            result["result"] = False

        return super().render(result, accepted_media_type, renderer_context)
