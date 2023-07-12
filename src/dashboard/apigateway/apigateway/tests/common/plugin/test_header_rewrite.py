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

from apigateway.common.plugin.header_rewrite import HeaderRewriteConvertor


class TestHeaderRewriteConvertor:
    @pytest.mark.parametrize(
        "transform_headers, expected",
        [
            (None, None),
            ({"set": {}, "delete": []}, None),
            ({"set": {"key1": "value1"}, "delete": ["key2"]}, {"set": {"key1": "value1"}, "remove": ["key2"]}),
        ],
    )
    def test_transform_headers_to_plugin_config(self, transform_headers, expected):
        assert HeaderRewriteConvertor.transform_headers_to_plugin_config(transform_headers) == expected

    @pytest.mark.parametrize(
        "stage_config, resource_config, expected",
        [
            (None, None, None),
            ({"set": {"key1": "value1"}, "remove": ["key2"]}, None, {"set": {"key1": "value1"}, "remove": ["key2"]}),
            (None, {"set": {"key1": "value1"}, "remove": ["key2"]}, {"set": {"key1": "value1"}, "remove": ["key2"]}),
            (
                {"set": {"key1": "value1", "key5": "value5"}, "remove": ["key2"]},
                {"set": {"key1": "value2", "key4": "value4"}, "remove": ["key2", "key3"]},
                {"set": {"key1": "value2", "key4": "value4", "key5": "value5"}, "remove": ["key2", "key3"]},
            ),
        ],
    )
    def test_merge_plugin_config(self, stage_config, resource_config, expected):
        assert HeaderRewriteConvertor.merge_plugin_config(stage_config, resource_config) == expected
