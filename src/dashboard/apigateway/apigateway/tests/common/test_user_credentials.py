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
from django.conf import settings

from apigateway.common.tenant.constants import TENANT_MODE_SINGLE_DEFAULT_TENANT_ID
from apigateway.common.tenant.user_credentials import (
    UserCredentials,
    get_user_credentials_from_request,
)


def test_get_user_access_token_from_request(mocker, faker):
    request = mocker.MagicMock(COOKIES={settings.BK_LOGIN_TICKET_KEY: "user_credentials"})
    assert get_user_credentials_from_request(request) == UserCredentials(
        credentials="user_credentials",
        tenant_id=TENANT_MODE_SINGLE_DEFAULT_TENANT_ID,
    )

    # No access_token
    request = mocker.MagicMock(COOKIES={})
    assert get_user_credentials_from_request(request) is None
