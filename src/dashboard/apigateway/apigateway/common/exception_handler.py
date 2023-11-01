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
from rest_framework import status
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

STATUS_CODE_DEFAULT_ERROR = {
    status.HTTP_400_BAD_REQUEST: error_codes.INVALID_ARGUMENT,
    status.HTTP_401_UNAUTHORIZED: error_codes.UNAUTHENTICATED,
    status.HTTP_403_FORBIDDEN: error_codes.NO_PERMISSION,
    status.HTTP_404_NOT_FOUND: error_codes.NOT_FOUND,
    status.HTTP_405_METHOD_NOT_ALLOWED: error_codes.METHOD_NOT_ALLOWED,
    status.HTTP_500_INTERNAL_SERVER_ERROR: error_codes.INTERNAL,
}


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


def custom_exception_handler(exc, context):  # noqa: PLR0911
    is_legacy = False
    request = context.get("request")
    if request and "/backend/api/v1/" in request.path:
        is_legacy = True

    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        error = error_codes.UNAUTHENTICATED
        return Response(error.code.as_json(is_legacy), status=error.code.status_code, headers={})

    if isinstance(exc, ValidationError):
        set_rollback()
        error = error_codes.INVALID_ARGUMENT.format(message=one_line_error(exc))
        return Response(error.code.as_json(is_legacy), status=error.code.status_code, headers={})

    if isinstance(exc, APIError):
        set_rollback()
        return Response(exc.code.as_json(is_legacy), status=exc.code.status_code, headers={})

    if isinstance(exc, MethodNotAllowed):
        set_rollback()
        error = error_codes.METHOD_NOT_ALLOWED.format(message=exc.detail)
        return Response(error.code.as_json(is_legacy), status=error.code.status_code, headers={})

    if isinstance(exc, PermissionDenied):
        set_rollback()
        error = error_codes.NO_PERMISSION.format(message=exc.detail, replace=True)
        return Response(error.code.as_json(is_legacy), status=error.code.status_code, headers={})

    # Call REST framework's default exception handler to get the standard error response.
    response = exception_handler(exc, context)
    # Use a default error code
    if response is not None:
        message = one_line_error(APIException(response.data))
        error_code = STATUS_CODE_DEFAULT_ERROR.get(response.status_code, error_codes.UNKNOWN)
        error = error_code.format(message=message, replace=True)
        return Response(error.code.as_json(is_legacy), status=response.status_code, headers={})

    logger.exception("unhandled error occurred")

    set_rollback()

    error = error_codes.UNKNOWN.format(message=str(exc))
    return Response(error.code.as_json(is_legacy), status=error.code.status_code, headers={})
