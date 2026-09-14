#
# TencentBlueKing is pleased to support the open source community by making
# BlueKing - APIGateway available.
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
from prometheus_client import CollectorRegistry

from apigateway.biz.sdk.metrics import create_sdk_generation_metrics


def test_sdk_metrics_use_only_bounded_labels():
    metrics = create_sdk_generation_metrics(CollectorRegistry())

    assert metrics.results._labelnames == ("language", "result", "error_class")
    assert metrics.phase_duration._labelnames == ("language", "phase", "result", "error_class")
    assert metrics.artifacts._labelnames == ("language", "distributor", "result")
    assert metrics.items._labelnames == ("result",)


def test_observe_phase_records_success_and_failure():
    metrics = create_sdk_generation_metrics(CollectorRegistry())

    with metrics.observe_phase("python", "generate"):
        pass

    try:
        with metrics.observe_phase("java", "build"):
            raise ValueError("failed")
    except ValueError:
        pass

    assert metrics.phase_duration.labels("python", "generate", "success", "none")._sum.get() >= 0
    samples = metrics.phase_duration.collect()[0].samples
    assert any(
        sample.name.endswith("_count")
        and sample.labels == {"language": "java", "phase": "build", "result": "failed", "error_class": "ValueError"}
        and sample.value == 1
        for sample in samples
    )
