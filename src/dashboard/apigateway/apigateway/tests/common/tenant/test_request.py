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

from unittest.mock import Mock, patch

from apigateway.common.tenant.request import gen_operation_tenant_header, get_user_tenant_id


@patch("apigateway.common.tenant.request.settings")
def test_get_user_tenant_id_multi_tenant_mode(mock_settings):
    mock_settings.ENABLE_MULTI_TENANT_MODE = True
    request = Mock()
    request.user.tenant_id = "tenant_123"
    assert get_user_tenant_id(request) == "tenant_123"


@patch("apigateway.common.tenant.request.settings")
def test_get_user_tenant_id_single_tenant_mode(mock_settings):
    mock_settings.ENABLE_MULTI_TENANT_MODE = False
    assert get_user_tenant_id(Mock()) == "default"


def test_gen_operation_tenant_headers():
    assert gen_operation_tenant_header() == {"X-Bk-Tenant-Id": "system"}
