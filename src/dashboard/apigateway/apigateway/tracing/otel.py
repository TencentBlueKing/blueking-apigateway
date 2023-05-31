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
import threading

from django.conf import settings
from opentelemetry import trace  # type: ignore
from opentelemetry.exporter.jaeger.thrift import JaegerExporter  # type: ignore
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GrpcSpanExporter  # type: ignore
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HttpSpanExporter  # type: ignore
from opentelemetry.sdk.resources import SERVICE_NAME, Resource  # type: ignore
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider  # type: ignore
from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
from opentelemetry.sdk.trace.sampling import _KNOWN_SAMPLERS  # type: ignore

from .constants import OTELTypeEnum
from .instrumentor import BKAppInstrumentor


class LazyBatchSpanProcessor(BatchSpanProcessor):
    def __init__(self, *args, **kwargs):
        super(LazyBatchSpanProcessor, self).__init__(*args, **kwargs)
        # 停止默认线程
        self.done = True
        with self.condition:
            self.condition.notify_all()
        self.worker_thread.join()
        self.done = False
        self.worker_thread = None

    def on_end(self, span: ReadableSpan) -> None:
        if self.worker_thread is None:
            self.worker_thread = threading.Thread(name=self.__class__.__name__, target=self.worker, daemon=True)
            self.worker_thread.start()
        super(LazyBatchSpanProcessor, self).on_end(span)

    def shutdown(self) -> None:
        # signal the worker thread to finish and then wait for it
        self.done = True
        with self.condition:
            self.condition.notify_all()
        if self.worker_thread:
            self.worker_thread.join()
        self.span_exporter.shutdown()


def setup_trace_config():
    if settings.IS_LOCAL:
        # local environment, use jaeger as trace service
        # docker run -p 16686:16686 -p 6831:6831/udp jaegertracing/all-in-one
        trace.set_tracer_provider(TracerProvider(resource=Resource.create({SERVICE_NAME: settings.OTEL_SERVICE_NAME})))
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=6831,
            udp_split_oversized_batches=True,
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

        if settings.OTEL_TYPE == OTELTypeEnum.GRPC.value:
            otlp_exporter = GrpcSpanExporter(endpoint=settings.OTEL_GRPC_HOST, insecure=True)
        elif settings.OTEL_TYPE == OTELTypeEnum.HTTP.value:
            otlp_exporter = HttpSpanExporter(endpoint=settings.OTEL_HTTP_URL, timeout=settings.OTEL_HTTP_TIMEOUT)
        else:
            raise ValueError(f"Unknown settings OTEL_TYPE: {settings.OTEL_TYPE}")

        # span_processor = BatchSpanProcessor(otlp_exporter)
        span_processor = LazyBatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)


def setup_by_settings():
    if getattr(settings, "ENABLE_OTEL_TRACE", False):
        setup_trace_config()
        BKAppInstrumentor().instrument()
