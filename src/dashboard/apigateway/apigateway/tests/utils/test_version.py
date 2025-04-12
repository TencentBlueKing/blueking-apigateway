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
    get_nex_version_with_type,
    get_next_version,
    is_version1_greater_than_version2,
    max_version,
    parse_version,
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

    @pytest.mark.parametrize(
        "version_str, expected",
        [
            # 标准语义化版本
            ("1.2.3", (1, 2, 3, None)),
            ("2.0.0-beta+exp.sha.5114f85", (2, 0, 0, "exp.sha.5114f85")),
            # 非标准版本
            ("3", (3, 0, 0, None)),
            ("4.5", (4, 5, 0, None)),
            ("v5.6.7-rc1", (5, 6, 7, None)),  # 需要预处理的情况
            ("6.7.8+prod", (6, 7, 8, "prod")),
            # 空值和非法格式
            ("", (0, 0, 0, None)),
        ],
    )
    def test_parse_version(self, version_str, expected):
        assert parse_version(version_str) == expected

    @pytest.mark.parametrize(
        "current_version, version_type, expected",
        [
            # 正常递增
            ("1.2.3", "major", "2.0.0"),
            ("1.2.3", "minor", "1.3.0"),
            ("1.2.3", "patch", "1.2.4"),
            # 带构建元数据
            ("1.0.0+prod", "major", "2.0.0+prod"),
            ("1.2.3-rc1+sha123", "minor", "1.3.0+sha123"),
            # 非标准版本
            ("3", "major", "4.0.0"),
            ("4.5", "patch", "4.5.1"),
            ("v5.6.7", "minor", "5.7.0"),  # 需要预处理的情况
            # 边界条件
            ("0.0.0", "major", "1.0.0"),
            ("", "minor", "0.1.0"),  # 空输入视为 0.0.0
        ],
    )
    def test_generate_new_version_normal(self, current_version, version_type, expected):
        assert get_nex_version_with_type(current_version, version_type) == expected

    @pytest.mark.parametrize(
        "current_version, version_type, expected_error",
        [
            # 非法版本类型
            ("1.2.3", "invalid_type", ValueError),
            # 非法版本格式（非数字部分）
            ("1.x.3", "major", ValueError),
            ("v2-three.4", "minor", ValueError),
        ],
    )
    def test_generate_new_version_error(self, current_version, version_type, expected_error):
        with pytest.raises(expected_error):
            get_nex_version_with_type(current_version, version_type)
