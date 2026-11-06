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

import pytest
from django.core.exceptions import ValidationError

from apigateway.apps.skill.validators import (
    normalize_tag_name,
    validate_skill_changelog,
    validate_skill_datetime,
    validate_skill_description,
    validate_skill_display_name,
    validate_skill_display_name_en,
    validate_skill_name,
    validate_skill_version,
)

EMOJI = "\U0001f600"


class TestValidateSkillName:
    @pytest.mark.parametrize("value", ["job-plan-run-and-log", "a", "abc123", "a" * 64])
    def test_valid(self, value):
        validate_skill_name(value)

    @pytest.mark.parametrize(
        "value, code",
        [
            ("", "min_length"),
            ("a" * 65, "max_length"),
            ("job--plan", "invalid"),
            ("-job", "invalid"),
            ("job-", "invalid"),
            ("Job-Plan", "invalid"),
            ("job_plan", "invalid"),
            ("job plan", "invalid"),
            ("job\n", "invalid"),
            ("执行作业", "invalid"),
        ],
    )
    def test_invalid(self, value, code):
        with pytest.raises(ValidationError) as exc_info:
            validate_skill_name(value)

        assert exc_info.value.code == code


class TestValidateSkillDisplayName:
    @pytest.mark.parametrize(
        "value",
        ["执行 JOB 作业方案", "执行作业方案并收集日志", "job-plan", "JOB 2", "a" * 64],
    )
    def test_valid(self, value):
        validate_skill_display_name(value)

    @pytest.mark.parametrize(
        "value, code",
        [
            ("", "min_length"),
            ("a" * 65, "max_length"),
            (" 执行作业方案", "invalid"),
            ("执行作业方案 ", "invalid"),
            ("执行  作业方案", "invalid"),
            ("执行_作业方案", "invalid"),
            ("执行作业方案!", "invalid"),
            (f"执行作业方案{EMOJI}", "invalid_char"),
        ],
    )
    def test_invalid(self, value, code):
        with pytest.raises(ValidationError) as exc_info:
            validate_skill_display_name(value)

        assert exc_info.value.code == code


class TestValidateSkillDisplayNameEn:
    @pytest.mark.parametrize("value", ["Run JOB Plan and Collect Logs", "Query IAM Policies", "bk-sops", "a" * 64])
    def test_valid(self, value):
        validate_skill_display_name_en(value)

    @pytest.mark.parametrize(
        "value, code",
        [
            ("", "min_length"),
            ("a" * 65, "max_length"),
            (" Run JOB Plan", "invalid"),
            ("Run JOB Plan ", "invalid"),
            ("Run  JOB Plan", "invalid"),
            ("Run_JOB_Plan", "invalid"),
            ("执行作业方案", "invalid"),
            (f"Run JOB Plan{EMOJI}", "invalid"),
        ],
    )
    def test_invalid(self, value, code):
        with pytest.raises(ValidationError) as exc_info:
            validate_skill_display_name_en(value)

        assert exc_info.value.code == code


class TestValidateSkillDescription:
    @pytest.mark.parametrize("value", ["执行作业平台（JOB、jobv3）的作业执行方案。", "a", "a" * 1024])
    def test_valid(self, value):
        validate_skill_description(value)

    @pytest.mark.parametrize(
        "value, code",
        [
            ("", "min_length"),
            ("a" * 1025, "max_length"),
            (f"执行作业方案{EMOJI}", "invalid_char"),
        ],
    )
    def test_invalid(self, value, code):
        with pytest.raises(ValidationError) as exc_info:
            validate_skill_description(value)

        assert exc_info.value.code == code


class TestValidateSkillChangelog:
    @pytest.mark.parametrize("value", ["", "- 首个版本", "a" * 10000])
    def test_valid(self, value):
        validate_skill_changelog(value)

    @pytest.mark.parametrize("value", [EMOJI, f"- 修复轮询条件{EMOJI}"])
    def test_invalid(self, value):
        with pytest.raises(ValidationError) as exc_info:
            validate_skill_changelog(value)

        assert exc_info.value.code == "invalid_char"


class TestValidateSkillVersion:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("1.0.0", "1.0.0"),
            ("1.1.1-alpha.1", "1.1.1-alpha.1"),
            ("1.0.0-Alpha", "1.0.0-alpha"),
            ("2.0.0+Build.1", "2.0.0+build.1"),
        ],
    )
    def test_valid(self, value, expected):
        assert validate_skill_version(value) == expected

    @pytest.mark.parametrize(
        "value, code",
        [
            ("", "min_length"),
            ("1.0.0-" + "a" * 59, "max_length"),
            ("v1.0.0", "invalid"),
            ("1.0", "invalid"),
            ("1.0.0\n", "invalid"),
            ("1١.0.0", "invalid"),
            ("1𝟘.0.0", "invalid"),
        ],
    )
    def test_invalid(self, value, code):
        with pytest.raises(ValidationError) as exc_info:
            validate_skill_version(value)

        assert exc_info.value.code == code


class TestValidateSkillDatetime:
    @pytest.mark.parametrize("value", ["2026-11-06T08:09:00Z", "2024-02-29T23:59:59Z"])
    def test_valid(self, value):
        validate_skill_datetime(value)

    @pytest.mark.parametrize(
        "value",
        [
            "2026-11-06",
            "2026-11-06 08:09:00",
            "2026-11-06T08:09:00+08:00",
            "2026-11-06T08:09:00.123Z",
            "2026-13-06T08:09:00Z",
            "2026-02-29T08:09:00Z",
            "2026-11-06T8:09:00Z",
        ],
    )
    def test_invalid(self, value):
        with pytest.raises(ValidationError) as exc_info:
            validate_skill_datetime(value)

        assert exc_info.value.code == "invalid"


class TestNormalizeTagName:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("作业运维", "作业运维"),
            ("  JOB  ", "job"),
            ("DevOps", "devops"),
            ("AI-运维", "ai-运维"),
            ("精选", "精选"),
            (" " + "a" * 64 + " ", "a" * 64),
        ],
    )
    def test_valid(self, value, expected):
        assert normalize_tag_name(value) == expected

    @pytest.mark.parametrize(
        "value, code",
        [
            ("", "min_length"),
            ("   ", "min_length"),
            ("a" * 65, "max_length"),
            (f"精选{EMOJI}", "invalid_char"),
        ],
    )
    def test_invalid(self, value, code):
        with pytest.raises(ValidationError) as exc_info:
            normalize_tag_name(value)

        assert exc_info.value.code == code
