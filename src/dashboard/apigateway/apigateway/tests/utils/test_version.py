#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the MIT License (the "License"); you may not use this file except
#  in compliance with the License. You may obtain a copy of the License at
#  #
#      http://opensource.org/licenses/MIT
#  #
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
#  either express or implied. See the License for the specific language governing permissions and
#  limitations under the License.
#  #
#  We undertake not to change the open source license (MIT license) applicable
#  to the current version of the project delivered to anyone in the future.
#  #
import pytest

from apigateway.utils.version import (
    _filter_the_valid_versions,
    get_next_version,
    is_version1_greater_than_version2,
    max_version,
)


class TestUtilsVersion:
    @pytest.mark.parametrize(
        "versions, expected",
        [
            (["1.0", "2.0", "invalid", "3.0"], ["1.0", "2.0", "3.0"]),
            (["a.b.c", "4.5.6"], ["4.5.6"]),
            ([], []),
        ],
    )
    def test_filter_the_valid_versions(self, versions, expected):
        result = _filter_the_valid_versions(versions)
        assert result == expected

    @pytest.mark.parametrize(
        "versions, expected",
        [
            (["1.0", "2.0", "3.0"], "3.0"),
            (["1.0", "invalid", "2.0"], "2.0"),
            (["invalid1", "invalid2"], "invalid2"),
            ([], ""),
        ],
    )
    def test_max_version(self, versions, expected):
        result = max_version(versions)
        assert result == expected

    @pytest.mark.parametrize(
        "current_version, expected_start",
        [
            ("1.2.3", "1.2.4"),
            ("1.0.0-alpha+001", "1.0.1"),  # The actual timestamp will be appended
            ("123456", "123456.0.1"),
            ("", ""),
        ],
    )
    def test_get_next_version(self, current_version, expected_start):
        result = get_next_version(current_version)
        assert result.startswith(expected_start)

    @pytest.mark.parametrize(
        "version1, version2, expected",
        [
            ("2.0", "1.0", True),
            ("1.0", "2.0", False),
            ("1.0", "invalid", False),
            ("invalid", "1.0", True),
        ],
    )
    def test_is_version1_greater_than_version2(self, version1, version2, expected):
        result = is_version1_greater_than_version2(version1, version2)
        assert result == expected
