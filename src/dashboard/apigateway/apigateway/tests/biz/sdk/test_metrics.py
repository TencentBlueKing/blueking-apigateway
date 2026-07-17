from prometheus_client import CollectorRegistry

from apigateway.biz.sdk.metrics import create_sdk_generation_metrics


def test_sdk_metrics_use_only_bounded_labels():
    metrics = create_sdk_generation_metrics(CollectorRegistry())

    assert metrics.results._labelnames == ("language", "status")
    assert metrics.phase_duration._labelnames == ("language", "phase", "status")
    assert metrics.artifacts._labelnames == ("language", "distributor", "status")
    assert metrics.items._labelnames == ("status",)


def test_observe_phase_records_success_and_failure():
    metrics = create_sdk_generation_metrics(CollectorRegistry())

    with metrics.observe_phase("python", "generate"):
        pass

    try:
        with metrics.observe_phase("java", "build"):
            raise ValueError("failed")
    except ValueError:
        pass

    assert metrics.phase_duration.labels("python", "generate", "success")._sum.get() >= 0
    samples = metrics.phase_duration.collect()[0].samples
    assert any(
        sample.name.endswith("_count")
        and sample.labels == {"language": "java", "phase": "build", "status": "failed"}
        and sample.value == 1
        for sample in samples
    )
