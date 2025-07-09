# -*- coding: utf-8 -*-
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

from unittest.mock import patch

from apigateway.common.security import is_forbidden_host


class TestIsForbiddenHost:
    """Test cases for is_forbidden_host function"""

    @patch("apigateway.common.security.settings")
    def test_hosts_with_forbidden_ports(self, mock_settings):
        """Test hosts with ports that are in FORBIDDEN_PORTS"""
        # Mock FORBIDDEN_PORTS to contain common forbidden ports
        mock_settings.FORBIDDEN_PORTS = [22, 3306]

        test_cases = [
            ("example.com", True),
            ("example.com:abc", False),
            ("example.com:22", False),
            ("192.168.1.1:3306", False),
            ("redis.example.com:1234", True),
            ("app.example.com:8080", True),
        ]

        for host, expected in test_cases:
            assert is_forbidden_host(host) == expected
