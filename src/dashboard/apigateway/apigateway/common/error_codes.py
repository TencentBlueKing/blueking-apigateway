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

    def as_json(self, is_legacy=False):
        if is_legacy:
            return {"result": False, "code": self.code, "message": self.message, "data": None}

        return {
            "error": {
                "code": self.code_name,
                "message": self.message,
            }
        }


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
        # TODO:
        # - remove all the `code`;
        # - 细化 validate_error
        ErrorCode("INVALID_ARGUMENT", 40002, _("校验失败"), status_code=status.HTTP_400_BAD_REQUEST),
        ErrorCode("FAILED_PRECONDITION", 40403, _("请求无法在当前系统状态下执行"), status_code=status.HTTP_400_BAD_REQUEST),
        ErrorCode("UNAUTHENTICATED", 40101, _("用户未登录或登录态失效，请使用登录链接重新登录"), status_code=status.HTTP_401_UNAUTHORIZED),
        ErrorCode("IAM_NO_PERMISSION", 40403, _("没有访问权限"), status_code=status.HTTP_403_FORBIDDEN),
        ErrorCode("NOT_FOUND", 40404, _("数据不存在"), status_code=status.HTTP_404_NOT_FOUND),
        ErrorCode("METHOD_NOT_ALLOWED", 40005, _("不支持当前的请求方法"), status_code=status.HTTP_405_METHOD_NOT_ALLOWED),
        ErrorCode("INTERNAL", 50103, _("处理请求时发生内部错误"), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR),
        ErrorCode("UNKNOWN", 40000, _("请求失败"), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR),
    ]
)
