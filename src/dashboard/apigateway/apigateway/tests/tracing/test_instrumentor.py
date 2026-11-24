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
import json

import pytest
import requests
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from apigateway.tracing.instrumentor import BKAppInstrumentor, requests_callback

pytestmark = pytest.mark.no_meta_schema


@pytest.fixture
def traced_request(mocker, settings):
    """Run the real Requests wrapper with the application's hook registration."""
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    mocker.patch("apigateway.tracing.instrumentor.LoggingInstrumentor")
    mocker.patch("apigateway.tracing.instrumentor.DjangoInstrumentor")
    mocker.patch("opentelemetry.instrumentation.requests.get_tracer", return_value=provider.get_tracer(__name__))
    settings.OTEL_INSTRUMENT_REDIS = False
    settings.OTEL_INSTRUMENT_CELERY = False
    settings.OTEL_INSTRUMENT_DB_API = False

    response = requests.Response()
    response.status_code = 200
    response._content = b"{}"
    mocker.patch.object(requests.adapters.HTTPAdapter, "send", return_value=response)
    BKAppInstrumentor()._instrument()

    def send(payload=None, *, body=None, status_code=200, headers=None, stream=False):
        exporter.clear()
        response.status_code = status_code
        response.headers.clear()
        response.headers.update(headers or {})
        response._content = body if body is not None else json.dumps(payload).encode()
        response._content_consumed = False
        with requests.Session() as session:
            result = session.get("https://component.example.test/api/", stream=stream)
        assert result is response
        spans = exporter.get_finished_spans()
        assert len(spans) == 1
        return result, spans[0]

    try:
        yield send
    finally:
        RequestsInstrumentor().uninstrument()
        provider.shutdown()


def test_business_failure_marks_span_error(traced_request):
    payload = {"code": 1, "message": "access_token=secret", "errors": {"bk_app_secret": "secret"}}
    response, span = traced_request(payload, headers={"x-bkapi-request-id": "gateway-request-1"})

    assert response.json() == payload
    assert span.status.status_code == StatusCode.ERROR
    assert span.attributes["result_code"] == 1
    assert span.attributes["request_id"] == "gateway-request-1"
    assert span.attributes["result_message"] == "[redacted]"
    assert span.attributes["result_errors"] == "[redacted]"
    assert "secret" not in repr(span.attributes)
    assert not span.events


@pytest.mark.parametrize("code", [0, "0", "00"])
def test_business_success_preserves_request_id(traced_request, code):
    _, span = traced_request({"code": code}, headers={"x-request-id": "iam-request-1"})

    assert span.status.status_code == StatusCode.OK
    assert span.attributes["result_code"] == 0
    assert span.attributes["request_id"] == "iam-request-1"


@pytest.mark.parametrize("code", [200, "200"])
def test_monitor_success_marks_span_ok(traced_request, code):
    payload = {"code": code, "result": True, "message": "OK", "data": {"series": []}}
    response, span = traced_request(payload, headers={"x-bkapi-request-id": "monitor-request-1"})

    assert response.json() == payload
    assert span.status.status_code == StatusCode.OK
    assert span.attributes["result_code"] == 200
    assert span.attributes["result_message"] == "[redacted]"
    assert span.attributes["request_id"] == "monitor-request-1"


@pytest.mark.parametrize(
    "payload",
    [
        {"code": 200, "result": False},
        {"code": "200", "result": False},
        {"code": 200},
        {"code": "200"},
        {"code": 1, "result": True},
        {"code": "1", "result": True},
    ],
)
def test_monitor_failure_marks_span_error(traced_request, payload):
    _, span = traced_request(payload)

    assert span.status.status_code == StatusCode.ERROR
    assert span.attributes["result_code"] == int(payload["code"])


@pytest.mark.parametrize(
    "headers, expected",
    [
        ({"x-bkapi-request-id": "gateway-id", "x-request-id": "iam-id"}, "gateway-id"),
        ({"x-request-id": "iam-id"}, "iam-id"),
        ({}, "legacy-id"),
    ],
)
def test_request_id_sources(traced_request, headers, expected):
    _, span = traced_request({"code": 0, "request_id": "legacy-id"}, headers=headers)
    assert span.attributes["request_id"] == expected


@pytest.mark.parametrize("body", [b"not JSON", b"[]", b"null", b'"text"'])
def test_non_object_response_is_ignored(traced_request, body):
    response, span = traced_request(body=body, headers={"x-request-id": "request-1"})

    assert response.content == body
    assert span.status.status_code == StatusCode.UNSET
    assert "result_code" not in span.attributes
    assert span.attributes["request_id"] == "request-1"
    assert not span.events


@pytest.mark.parametrize("status_code", [400, 500])
@pytest.mark.parametrize("payload", [{"code": 0}, {"code": 200, "result": True}, {"code": "200", "result": True}])
def test_http_error_status_is_preserved(traced_request, status_code, payload):
    _, span = traced_request(payload, status_code=status_code)
    assert span.status.status_code == StatusCode.ERROR


@pytest.mark.parametrize(
    "code", ["secret-token", {"access_token": "secret"}, [0], None, False, 0.5, 2**64, "9" * 1000]
)
def test_invalid_code_cannot_leak_or_raise(traced_request, code):
    _, span = traced_request({"code": code})
    assert span.status.status_code == StatusCode.ERROR
    assert span.attributes["result_code"] == "[invalid]"
    assert not span.events


@pytest.mark.parametrize("code", [-(2**63), 2**63 - 1, str(2**63 - 1), "-1"])
def test_valid_nonzero_business_code_is_preserved(traced_request, code):
    _, span = traced_request({"code": code})
    assert span.status.status_code == StatusCode.ERROR
    assert span.attributes["result_code"] == int(code)


def test_maximum_length_request_id_is_preserved(traced_request):
    _, span = traced_request({"code": 0, "request_id": "x" * 128})
    assert span.attributes["request_id"] == "x" * 128


def test_missing_code_retains_legacy_success_behavior(traced_request):
    _, span = traced_request({"result": True})
    assert span.status.status_code == StatusCode.OK
    assert span.attributes["result_code"] == 0


@pytest.mark.parametrize("field", ["message", "errors"])
@pytest.mark.parametrize("value", ["secret" * 1000, {"token": "secret"}, ["secret", {"password": "secret"}]])
def test_error_metadata_is_redacted_and_bounded(traced_request, field, value):
    _, span = traced_request({"code": 1, field: value, "data": {"token": "secret"}})
    assert span.attributes[f"result_{field}"] == "[redacted]"
    assert "secret" not in repr(span.attributes)
    assert not span.events


@pytest.mark.parametrize("request_id", ["x" * 129, "token=secret", "line\nbreak", {"token": "secret"}, 123])
def test_invalid_body_request_id_is_omitted(traced_request, request_id):
    _, span = traced_request({"code": 0, "request_id": request_id})
    assert span.status.status_code == StatusCode.OK
    assert "request_id" not in span.attributes
    assert not span.events


@pytest.mark.parametrize("request_id", ["x" * 129, "token=secret", "line\nbreak"])
def test_invalid_header_request_id_is_omitted(traced_request, request_id):
    _, span = traced_request({"code": 0}, headers={"x-request-id": request_id})
    assert "request_id" not in span.attributes


def test_streamed_response_body_is_not_parsed(traced_request, mocker):
    parse = mocker.patch.object(requests.Response, "json", side_effect=AssertionError("stream must remain unread"))
    response, span = traced_request({"code": 1}, stream=True, headers={"x-request-id": "stream-id"})
    assert not response._content_consumed
    parse.assert_not_called()
    assert "result_code" not in span.attributes
    assert span.attributes["request_id"] == "stream-id"


def test_json_parsing_failure_cannot_break_request(traced_request, mocker):
    mocker.patch.object(requests.Response, "json", side_effect=RuntimeError("secret response"))
    _, span = traced_request({"code": 1})
    assert "secret" not in repr(span.attributes)
    assert not span.events


def test_non_recording_span_does_not_parse_response(mocker):
    span = mocker.Mock()
    span.is_recording.return_value = False
    response = mocker.Mock()
    requests_callback(span, requests.Request("GET", "https://component.example.test/").prepare(), response)
    response.json.assert_not_called()
    span.set_attribute.assert_not_called()
