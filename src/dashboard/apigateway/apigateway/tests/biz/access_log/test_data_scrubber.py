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
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智dashboard.apigateway.apigateway.biz.access_log.exceptionsle.
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
import pytest

from apigateway.biz.access_log.data_scrubber import DataScrubber
from apigateway.biz.access_log.exceptions import NotScrubbedException


class TestDataScrubber:
    @pytest.mark.parametrize(
        "content, expected",
        [
            ("", False),
            ('{"app_code": "test"}', False),
            ('{"app_secret": "xxx"}', True),
            ('{"bk_ticket": "xxx"}', True),
        ],
    )
    def test_contains_sensitive_data(self, content, expected):
        data_scrubber = DataScrubber()
        result = data_scrubber._contains_sensitive_data(content)
        assert result is expected

    @pytest.mark.parametrize(
        "content, expected",
        [
            # ok, json data, matched sensitive key
            (
                '{"app_code": "test", "app_secret": "xxx"}',
                '{"app_code": "test", "app_secret": "***"}',
            ),
            # ok, urlencoded data, matched sensitive key
            (
                "app_code=test&app_secret=test",
                "app_code=test&app_secret=%2A%2A%2A",
            ),
            # ok, json data, part matched sensitive key
            (
                '{"app_code": "test", "my_password": "xxx"}',
                '{"app_code": "test", "my_password": "***"}',
            ),
        ],
    )
    def test_scrub_body(self, content, expected):
        data_scrubber = DataScrubber()
        result = data_scrubber._scrub_body(content)
        assert result == expected

    @pytest.mark.parametrize(
        "content",
        [
            # error, invalid json data
            '{"app_code": "test", "app_secr',
            # error, invalid urlencoded data
            "a=b&cd",
        ],
    )
    def test_scrub_body__error(self, content):
        data_scrubber = DataScrubber()
        with pytest.raises(NotScrubbedException):
            data_scrubber._scrub_body(content)

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                # ok, matched
                {
                    "app_code": "test",
                    "app_secret": "test",
                },
                {
                    "app_code": "test",
                    "app_secret": "***",
                },
            ),
            # ok, part matched
            (
                {
                    "app_code": "test",
                    "my_password": "test",
                },
                {
                    "app_code": "test",
                    "my_password": "***",
                },
            ),
            # ok, no sensitive data
            (
                {
                    "app_code": "test",
                    "at": "test",
                },
                {
                    "app_code": "test",
                    "at": "test",
                },
            ),
            # ok, some value is empty
            (
                {
                    "app_code": "test",
                    "at": "",
                },
                {
                    "app_code": "test",
                    "at": "",
                },
            ),
        ],
    )
    def test_scrub_by_keys(self, data, expected):
        data_scrubber = DataScrubber()
        result = data_scrubber._scrub_by_keys(data)
        assert result == expected
