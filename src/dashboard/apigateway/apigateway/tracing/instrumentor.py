#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from __future__ import annotations

import json
import re
from http import HTTPStatus
from typing import TYPE_CHECKING, Collection

from django.conf import settings
from opentelemetry.instrumentation import dbapi  # type: ignore
from opentelemetry.instrumentation.django import DjangoInstrumentor  # type: ignore
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor  # type: ignore
from opentelemetry.instrumentation.logging import LoggingInstrumentor  # type: ignore
from opentelemetry.instrumentation.requests import RequestsInstrumentor  # type: ignore
from opentelemetry.trace import Span, Status, StatusCode, format_trace_id  # type: ignore

if TYPE_CHECKING:
    from requests import PreparedRequest, Response


def _get_result_code(value) -> int | str:
    # Only export numeric business codes within OpenTelemetry's signed int64 range.
    if isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]{1,19}", value):
        value = int(value)
    if type(value) is int and -(2**63) <= value < 2**63:
        return value
    return "[invalid]"


def _set_request_id(span: Span, value):
    # Request IDs are opaque identifiers, never arbitrary response text or objects.
    if isinstance(value, str) and re.fullmatch(r"[a-zA-Z0-9_.:-]{1,128}", value):
        span.set_attribute("request_id", value)


def requests_callback(span: Span, prepared_request: PreparedRequest, response: Response):
    """处理蓝鲸标准协议响应，限制并脱敏业务元数据。"""
    if not span.is_recording():
        return

    request_id = response.headers.get("x-bkapi-request-id") or response.headers.get("x-request-id")
    _set_request_id(span, request_id)

    # Session.send has read non-streaming bodies before this hook. Never consume
    # an unread stream solely for tracing; header request IDs are still available.
    if not getattr(response, "_content_consumed", False):
        return

    try:
        json_result = response.json()
    except Exception:  # pylint: disable=broad-except
        return

    if not isinstance(json_result, dict):
        return

    # Legacy ESB uses "00"; BK Monitor uses 200 with a true result.
    # Leave HTTP error statuses set by the upstream instrumentation intact.
    if response.status_code == HTTPStatus.OK.value:
        code = _get_result_code(json_result.get("code", 0))
        span.set_attribute("result_code", code)
        success = code == 0 or (code == HTTPStatus.OK.value and bool(json_result.get("result")))
        span.set_status(Status(StatusCode.OK if success else StatusCode.ERROR))

    # Free-form messages and nested errors can contain credentials even without
    # sensitive key names. Keep only their presence, with a fixed-size mask.
    span.set_attribute("result_message", "[redacted]" if json_result.get("message") else "")
    if json_result.get("errors"):
        span.set_attribute("result_errors", "[redacted]")

    if not request_id:
        _set_request_id(span, json_result.get("request_id"))


def django_request_hook(span, request):
    """
    在request注入trace_id，方便获取
    """
    trace_id = span.get_span_context().trace_id
    request.otel_trace_id = format_trace_id(trace_id)


def django_response_hook(span, request, response):
    """
    处理蓝鲸标准协议 Django 响应
    """
    # the status of non-200 should not be changed
    if response.status_code != HTTPStatus.OK.value:
        return

    if hasattr(response, "data"):
        result = response.data
    else:
        try:
            result = json.loads(response.content)
        except Exception:  # pylint: disable=broad-except
            return
    if not isinstance(result, dict):
        return

    code = result.get("code", 0)
    try:
        code = int(code)
    except Exception:  # pylint: disable=broad-except
        pass
    if code in [0, "0", "00"]:
        span.set_status(Status(StatusCode.OK))
    else:
        span.set_status(Status(StatusCode.ERROR))

    span.set_attribute("result_code", code)
    span.set_attribute("result_message", result.get("message", ""))

    errors = result.get("errors", "")
    if errors:
        span.set_attribute("result_errors", errors)

    request_id = response.headers.get("x-request-id")
    if request_id:
        span.set_attribute("request_id", request_id)


class BKAppInstrumentor(BaseInstrumentor):
    def instrumentation_dependencies(self) -> Collection[str]:
        return []

    def _instrument(self, **kwargs):
        LoggingInstrumentor().instrument()
        # print("otel instructment: logging")

        RequestsInstrumentor().instrument(response_hook=requests_callback)
        # print("otel instructment: requests")

        DjangoInstrumentor().instrument(request_hook=django_request_hook, response_hook=django_response_hook)
        # print("otel instructment: django")

        if getattr(settings, "OTEL_INSTRUMENT_REDIS", False):
            from opentelemetry.instrumentation.redis import RedisInstrumentor  # noqa

            RedisInstrumentor().instrument()
            print("otel instructment: redis")

        if getattr(settings, "OTEL_INSTRUMENT_CELERY", False):
            from opentelemetry.instrumentation.celery import CeleryInstrumentor  # noqa

            CeleryInstrumentor().instrument()
            print("otel instructment: celery")

        if getattr(settings, "OTEL_INSTRUMENT_DB_API", False):
            import pymysql  # noqa

            dbapi.wrap_connect(
                __name__,
                pymysql.connect,
                "connect",
                "mysql",
                {"database": "db", "port": "port", "host": "host", "user": "user"},
            )
            print("otel instructment: database api")

    def _uninstrument(self, **kwargs):
        for instrumentor in self.instrumentors:
            print("otel uninstrument", instrumentor)
            instrumentor.uninstrument()
