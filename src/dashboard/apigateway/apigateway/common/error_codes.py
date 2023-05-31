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
import copy

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class APIError(APIException):
    """A common API Error"""

    delimiter = ": "

    def __init__(self, code):
        self.code = code
        super(APIError, self).__init__(str(self))

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.code.status_code}({self.code.code_name}-{self.code.message})>"

    def format(self, message=None, replace=False, **kwargs):
        """Using a customized message for this ErrorCode

        :param str message: if not given, default message will be used
        :param bool replace: relace default message if true
        """
        self.code = copy.copy(self.code)
        if message:
            if replace:
                self.code.message = message
            else:
                self.code.message += "%s%s" % (self.delimiter, message)

        # Render message string
        if kwargs:
            self.code.message = self.code.message.format(**kwargs)

        return self


class ErrorCode:
    """Error code"""

    def __init__(self, code_name: str, code: int, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.code_name = code_name
        self.code = code
        self.message = message
        self.status_code = status_code

    def as_json(self):
        return {"result": False, "code": self.code, "message": self.message, "data": None}


class ErrorCodeCollection:
    """A collection of ErrorCodes"""

    def __init__(self):
        self._error_codes_dict = {}

    def add_code(self, error_code):
        self._error_codes_dict[error_code.code_name] = error_code

    def add_codes(self, code_list):
        for error_code in code_list:
            self.add_code(error_code)

    def __getattr__(self, code_name):
        error_code = self._error_codes_dict[code_name]
        return APIError(error_code)


error_codes = ErrorCodeCollection()
error_codes.add_codes(
    [
        # 通用错误
        ErrorCode("COMMON_ERROR", 40000, _("请求失败")),
        ErrorCode("VALIDATE_ERROR", 40002, _("校验失败")),
        ErrorCode("COMPONENT_ERROR", 40003, _("请求第三方接口失败")),
        ErrorCode("REMOTE_REQUEST_ERROR", 40003, _("请求第三方接口错误")),
        ErrorCode("JSON_FORMAT_ERROR", 40004, _("Json格式错误")),
        ErrorCode("METHOD_NOT_ALLOWED", 40005, _("不支持当前的请求方法")),
        ErrorCode("INVALID_ARGS", 40006, _("参数错误")),
        ErrorCode("SDK_ERROR", 50100, _("网关SDK生成或上传失败")),
        ErrorCode("RESOURCE_DOC_EXPORT_ERROR", 50101, _("网关文档导出失败")),
        ErrorCode("RESOURCE_DOC_IMPORT_ERROR", 50102, _("资源文档导入失败")),
        # ESB 对应的网关不存在
        ErrorCode("COMPONENT_GATEWAY_NOT_FOUND", 50203, _("组件对应的网关 [name={api_name}] 不存在")),
        ErrorCode("COMPONENT_METHOD_INVALID", 50204, _("组件请求方法配置错误")),
        # 未登录
        ErrorCode("UNAUTHORIZED", 40101, _("用户未登录或登录态失效，请使用登录链接重新登录"), status_code=status.HTTP_401_UNAUTHORIZED),
        ErrorCode("FORBIDDEN", 40403, _("没有访问权限")),
        ErrorCode("NOT_FOUND_ERROR", 40404, _("数据不存在"), status_code=status.HTTP_404_NOT_FOUND),
        # Elasticsearch错误
        ErrorCode("ES_HOST_EMPTY_ERROR", 40501, _("系统未配置 Elasticsearch 地址")),
        ErrorCode("ES_CONNECTION_ERROR", 40502, _("连接 Elasticsearch {es_hosts_display} 出现错误: {err}，请检查服务是否正常")),
        ErrorCode(
            "ES_CONNECTION_TIMEOUT", 40503, _("请求 Elasticsearch {es_hosts_display} 超时（read timeout={timeout}），请稍后重试")
        ),
        ErrorCode(
            "ES_INDEX_NOT_FOUND", 40505, _("请求 Elasticsearch {es_hosts_display} 出现错误，elasticsearch index {index} 不存在")
        ),
        ErrorCode("ES_AUTHENTICATION_ERROR", 40506, _("请求 Elasticsearch {es_hosts_display} 认证失败，请检查认证信息是否正确")),
        ErrorCode("ES_SEARCH_ERROR", 40507, _("请求 Elasticsearch {es_hosts_display} 出现错误: {err}，请联系系统负责人处理")),
    ]
)
