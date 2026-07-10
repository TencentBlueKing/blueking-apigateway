"""Low-cardinality Prometheus metrics for SDK generation."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from time import monotonic
from typing import TYPE_CHECKING

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge, Histogram

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
        status = "success"
        try:
            yield
        except Exception:
            status = "failed"
            raise
        finally:
            self.phase_duration.labels(language, phase, status).observe(monotonic() - started)

    def record_result(self, language: str, status: str) -> None:
        self.results.labels(language, status).inc()

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
            ("language", "status"),
            registry=registry,
        ),
        phase_duration=Histogram(
            "bk_apigateway_sdk_generation_phase_duration_seconds",
            "SDK generation phase duration.",
            ("language", "phase", "status"),
            registry=registry,
        ),
        artifacts=Counter(
            "bk_apigateway_sdk_generation_artifacts_total",
            "SDK artifacts handled by distributor.",
            ("language", "distributor", "status"),
            registry=registry,
        ),
        items=Gauge(
            "bk_apigateway_sdk_generation_items",
            "Current SDK generation item count by status.",
            ("status",),
            registry=registry,
        ),
    )


sdk_generation_metrics = create_sdk_generation_metrics()
