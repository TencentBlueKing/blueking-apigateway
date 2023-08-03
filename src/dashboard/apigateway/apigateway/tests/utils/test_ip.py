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


import pytest

from apigateway.utils.ip import parse_ip_content_to_list


class TestIP:
    @pytest.mark.parametrize(
        "ip_content, expected",
        [
            ("", []),
            ("1.1.1.1", ["1.1.1.1"]),
            ("1.1.1.1\n2.2.2.2 \r\n#comment\n 1.1.1.1", ["1.1.1.1", "2.2.2.2"]),
            ("::ffff:192.1.1.1", ["::ffff:192.1.1.1"]),
            ("::ffff:192.1.1.1/96", ["::ffff:c001:101/96"]),
            ("0:0:0:0:0:ffff:192.1.1.1/96", ["::ffff:c001:101/96"]),
        ],
    )
    def test_parse_ip_content_to_list(self, ip_content, expected):
        assert sorted(parse_ip_content_to_list(ip_content)) == sorted(expected)
