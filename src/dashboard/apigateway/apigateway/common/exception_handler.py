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

from blue_krill.web.drf_utils import stringify_validation_error
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnList
from rest_framework.views import exception_handler, set_rollback

from apigateway.common.error_codes import APIError, error_codes

logger = logging.getLogger(__name__)


def one_line_error(error: ValidationError):
    """Extract one line error from ValidationError"""
    try:
        # 处理 many=True 场景，找出第几个数据出现的错误
        if isinstance(error.detail, (ReturnList, list, tuple)):
            for index, err in enumerate(error.detail):
                if err == {}:
                    continue

                return "index={index}, {error}".format(index=index, error=stringify_validation_error(error)[0])

        return stringify_validation_error(error)[0]
    except Exception:
        logger.exception("Error getting one line error from %s", error)
        return "format error message failed"


def custom_exception_handler(exc, context):
    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        error = error_codes.UNAUTHORIZED
        return Response(error.code.as_json(), status=error.code.status_code, headers={})

    elif isinstance(exc, ValidationError):
        set_rollback()
        error = error_codes.VALIDATE_ERROR.format(message=one_line_error(exc))
        return Response(error.code.as_json(), status=error.code.status_code, headers={})

    elif isinstance(exc, APIError):
        set_rollback()
        return Response(exc.code.as_json(), status=exc.code.status_code, headers={})

    elif isinstance(exc, MethodNotAllowed):
        set_rollback()
        error = error_codes.METHOD_NOT_ALLOWED.format(message=exc.detail)
        return Response(error.code.as_json(), status=error.code.status_code, headers={})

    elif isinstance(exc, PermissionDenied):
        set_rollback()
        error = error_codes.FORBIDDEN.format(message=exc.detail, replace=True)
        return Response(error.code.as_json(), status=error.code.status_code, headers={})

    # Call REST framework's default exception handler to get the standard error response.
    response = exception_handler(exc, context)
    # Use a default error code
    if response is not None:
        error = error_codes.COMMON_ERROR.format(message=one_line_error(APIException(response.data)), replace=True)
        return Response(error.code.as_json(), status=response.status_code, headers={})

    logger.exception("unhandled error occurred")

    set_rollback()
    error = error_codes.COMMON_ERROR.format(message=str(exc))
    return Response(error.code.as_json(), status=error.code.status_code, headers={})
