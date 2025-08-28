#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from django.conf import settings
from opentelemetry import trace  # type: ignore
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GrpcSpanExporter  # type: ignore
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HttpSpanExporter  # type: ignore
from opentelemetry.sdk.resources import SERVICE_NAME, Resource  # type: ignore
from opentelemetry.sdk.trace import TracerProvider  # type: ignore
from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
from opentelemetry.sdk.trace.sampling import _KNOWN_SAMPLERS  # type: ignore

from .constants import OTELTypeEnum
from .instrumentor import BKAppInstrumentor


def setup_trace_config():
    if settings.IS_LOCAL:
        # local environment, use jaeger as trace service
        # docker run -p 16686:16686 -p 6831:6831/udp jaegertracing/all-in-one
        trace.set_tracer_provider(TracerProvider(resource=Resource.create({SERVICE_NAME: settings.OTEL_SERVICE_NAME})))
        jaeger_exporter = GrpcSpanExporter(
            endpoint="localhost:4317",
            insecure=True,
        )
        trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(jaeger_exporter))
    else:
        trace.set_tracer_provider(
            tracer_provider=TracerProvider(
                resource=Resource.create(
                    {
                        "service.name": settings.OTEL_SERVICE_NAME,
                        "bk.data.token": settings.OTEL_DATA_TOKEN,
                    },
                ),
                sampler=_KNOWN_SAMPLERS[settings.OTEL_SAMPLER],
            )
        )

        if OTELTypeEnum.GRPC.value == settings.OTEL_TYPE:  # ruff: noqa: SIM300
            otlp_exporter = GrpcSpanExporter(endpoint=settings.OTEL_GRPC_HOST, insecure=True)
        elif OTELTypeEnum.HTTP.value == settings.OTEL_TYPE:  # ruff: noqa: SIM300
            otlp_exporter = HttpSpanExporter(endpoint=settings.OTEL_HTTP_URL, timeout=settings.OTEL_HTTP_TIMEOUT)
        else:
            raise ValueError(f"Unknown settings OTEL_TYPE: {settings.OTEL_TYPE}")

        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)


def setup_by_settings():
    if getattr(settings, "ENABLE_OTEL_TRACE", False):
        setup_trace_config()
        BKAppInstrumentor().instrument()
