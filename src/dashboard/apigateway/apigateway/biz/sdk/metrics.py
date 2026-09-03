"""Low-cardinality Prometheus metrics for SDK generation."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from time import monotonic
from typing import TYPE_CHECKING

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge, Histogram

from apigateway.biz.sdk.exceptions import SDKGenerationError

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping


@dataclass(frozen=True)
class SDKGenerationMetrics:
    results: Counter
    phase_duration: Histogram
    artifacts: Counter
    items: Gauge

    @contextmanager
    def observe_phase(self, language: str, phase: str) -> Iterator[None]:
        started = monotonic()
        result = "success"
        error_class = "none"
        try:
            yield
        except Exception as error:
            result = "failed"
            error_class = error.code if isinstance(error, SDKGenerationError) else error.__class__.__name__
            raise
        finally:
            self.phase_duration.labels(language, phase, result, error_class).observe(monotonic() - started)

    def record_result(self, language: str, result: str, error_class: str = "none") -> None:
        self.results.labels(language, result, error_class).inc()

    def record_artifacts(self, language: str, distributor: str, status: str, count: int = 1) -> None:
        self.artifacts.labels(language, distributor, status).inc(count)

    def set_item_counts(self, counts: Mapping[str, int]) -> None:
        for status, count in counts.items():
            self.items.labels(status).set(count)


def create_sdk_generation_metrics(registry: CollectorRegistry = REGISTRY) -> SDKGenerationMetrics:
    return SDKGenerationMetrics(
        results=Counter(
            "bk_apigateway_sdk_generation_results_total",
            "Completed SDK generation items.",
            ("language", "result", "error_class"),
            registry=registry,
        ),
        phase_duration=Histogram(
            "bk_apigateway_sdk_generation_phase_duration_seconds",
            "SDK generation phase duration.",
            ("language", "phase", "result", "error_class"),
            registry=registry,
        ),
        artifacts=Counter(
            "bk_apigateway_sdk_generation_artifacts_total",
            "SDK artifacts handled by distributor.",
            ("language", "distributor", "result"),
            registry=registry,
        ),
        items=Gauge(
            "bk_apigateway_sdk_generation_items",
            "Current SDK generation item count by status.",
            ("result",),
            registry=registry,
        ),
    )


sdk_generation_metrics = create_sdk_generation_metrics()
