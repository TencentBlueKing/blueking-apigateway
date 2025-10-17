#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

import unittest
from unittest.mock import Mock

from apigateway.controller.convertor.route import MATCH_SUB_PATH_PRIORITY, RouteConvertor


class TestRouteConvertor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock the required dependencies
        self.mock_release_data = Mock()
        self.mock_backend_service_mapping = {1: "test-service-id"}
        self.mock_publish_id = None
        self.mock_revoke_flag = False

        # Create RouteConvertor instance
        self.convertor = RouteConvertor(
            release_data=self.mock_release_data,
            backend_service_mapping=self.mock_backend_service_mapping,
            publish_id=self.mock_publish_id,
            revoke_flag=self.mock_revoke_flag,
        )

    def test_calculate_match_subpath_route_priority(self):
        """Test _calculate_match_subpath_route_priority method with various path inputs."""
        test_cases = [
            {
                "name": "test",
                "path": "a/b/c",
                "expected": MATCH_SUB_PATH_PRIORITY + 5,  # len("a/b/c") = 5
            },
            {
                "name": "test_with_args",
                "path": "a/:abc/c",
                "expected": MATCH_SUB_PATH_PRIORITY + 5,  # len("a/a/c") = 5 after replacement
            },
            {
                "name": "test_empty",
                "path": "",
                "expected": MATCH_SUB_PATH_PRIORITY,  # len("") = 0
            },
            {
                "name": "test_ok",
                "path": "a/abc/c",
                "expected": MATCH_SUB_PATH_PRIORITY + 7,  # len("a/abc/c") = 7
            },
            {
                "name": "test_single_segment",
                "path": "test",
                "expected": MATCH_SUB_PATH_PRIORITY + 4,  # len("test") = 4
            },
            {
                "name": "test_multiple_params",
                "path": ":id/:name/:type",
                "expected": MATCH_SUB_PATH_PRIORITY + 5,  # len("a/a/a") = 5 after replacement
            },
            {
                "name": "test_mixed_params_and_static",
                "path": "api/:version/users/:id",
                "expected": MATCH_SUB_PATH_PRIORITY + 15,  # len("api/a/users/a") = 15 after replacement
            },
            {
                "name": "test_single_slash",
                "path": "/",
                "expected": MATCH_SUB_PATH_PRIORITY + 1,  # len("/") = 1
            },
            {
                "name": "test_nested_path",
                "path": "api/v1/users/:id/profile",
                "expected": MATCH_SUB_PATH_PRIORITY + 17,  # len("api/v1/users/a/profile") = 17 after replacement
            },
        ]

        for test_case in test_cases:
            with self.subTest(name=test_case["name"]):
                result = self.convertor._calculate_match_subpath_route_priority(test_case["path"])
                self.assertEqual(
                    result,
                    test_case["expected"],
                    f"Failed for path '{test_case['path']}': expected {test_case['expected']}, got {result}",
                )

    def test_calculate_match_subpath_route_priority_edge_cases(self):
        """Test edge cases for _calculate_match_subpath_route_priority method."""
        # Test with only colons (should be replaced with 'a')
        result = self.convertor._calculate_match_subpath_route_priority(":::")
        expected = MATCH_SUB_PATH_PRIORITY + 3  # len("aaa") = 3
        self.assertEqual(result, expected)

        # Test with empty segments
        result = self.convertor._calculate_match_subpath_route_priority("a//b")
        expected = MATCH_SUB_PATH_PRIORITY + 4  # len("a//b") = 4
        self.assertEqual(result, expected)

        # Test with leading and trailing slashes
        result = self.convertor._calculate_match_subpath_route_priority("/a/b/")
        expected = MATCH_SUB_PATH_PRIORITY + 5  # len("/a/b/") = 5
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
