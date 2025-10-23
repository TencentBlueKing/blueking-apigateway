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

from apigateway.controller.convertor import constants


class TestConvertorConstants:
    """Test convertor constants"""

    def test_default_apisix_version(self):
        """Test DEFAULT_APISIX_VERSION constant"""
        assert constants.DEFAULT_APISIX_VERSION == "3.13"

    def test_label_keys(self):
        """Test label key constants"""
        assert constants.LABEL_KEY_GATEWAY == "gateway.bk.tencent.com/gateway"
        assert constants.LABEL_KEY_STAGE == "gateway.bk.tencent.com/stage"
        assert constants.LABEL_KEY_APISIX_VERSION == "gateway.bk.tencent.com/apisix-version"
        assert constants.LABEL_KEY_PUBLISH_ID == "gateway.bk.tencent.com/publish-id"
        assert constants.LABEL_KEY_BACKEND_ID == "gateway.bk.tencent.com/backend-id"

    def test_subpath_param_name(self):
        """Test SUBPATH_PARAM_NAME constant"""
        assert constants.SUBPATH_PARAM_NAME == "bk_api_subpath_match_param_name"

    def test_match_sub_path_priority(self):
        """Test MATCH_SUB_PATH_PRIORITY constant"""
        assert constants.MATCH_SUB_PATH_PRIORITY == -1000

    def test_label_keys_are_strings(self):
        """Test that all label keys are strings"""
        assert isinstance(constants.LABEL_KEY_GATEWAY, str)
        assert isinstance(constants.LABEL_KEY_STAGE, str)
        assert isinstance(constants.LABEL_KEY_APISIX_VERSION, str)
        assert isinstance(constants.LABEL_KEY_PUBLISH_ID, str)
        assert isinstance(constants.LABEL_KEY_BACKEND_ID, str)

    def test_label_keys_are_unique(self):
        """Test that all label keys are unique"""
        keys = [
            constants.LABEL_KEY_GATEWAY,
            constants.LABEL_KEY_STAGE,
            constants.LABEL_KEY_APISIX_VERSION,
            constants.LABEL_KEY_PUBLISH_ID,
            constants.LABEL_KEY_BACKEND_ID,
        ]
        assert len(keys) == len(set(keys))
