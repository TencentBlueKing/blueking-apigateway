# -*- coding: utf-8 -*-
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

from apigateway.components.bkuser import query_display_names_for_readonly


def test_query_display_names_for_readonly_preserves_input_order(mocker):
    mock_query_display_names_cached = mocker.patch(
        "apigateway.components.bkuser.query_display_names_cached",
        return_value=[
            {"bk_username": "alice", "display_name": "Alice"},
            {"bk_username": "bob", "display_name": "Bob"},
        ],
    )
    bk_usernames = ["bob", "alice"]

    result = query_display_names_for_readonly("tenant-a", bk_usernames)

    assert result == ["Bob", "Alice"]
    assert bk_usernames == ["bob", "alice"]
    mock_query_display_names_cached.assert_called_once_with("tenant-a", "alice,bob")
