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

from apigateway.controller import constants


class TestConstants:
    """Test constants values"""

    def test_no_need_report_event_publish_id(self):
        """Test NO_NEED_REPORT_EVENT_PUBLISH_ID constant"""
        assert constants.NO_NEED_REPORT_EVENT_PUBLISH_ID == -1

    def test_delete_publish_id(self):
        """Test DELETE_PUBLISH_ID constant"""
        assert constants.DELETE_PUBLISH_ID == -2

    def test_publish_id_constants_are_negative(self):
        """Test that all special publish IDs are negative to avoid conflicts with real IDs"""
        assert constants.NO_NEED_REPORT_EVENT_PUBLISH_ID < 0
        assert constants.DELETE_PUBLISH_ID < 0

    def test_publish_id_constants_are_unique(self):
        """Test that all special publish IDs are unique"""
        assert constants.NO_NEED_REPORT_EVENT_PUBLISH_ID != constants.DELETE_PUBLISH_ID
