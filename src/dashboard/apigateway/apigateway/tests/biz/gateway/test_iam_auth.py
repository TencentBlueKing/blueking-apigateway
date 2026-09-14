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
import pytest

from apigateway.biz.gateway.iam_auth import (
    clear_gateway_iam_auth_cache,
    is_iam_auth_active,
    is_iam_gateway_action_allowed,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_auth_cache():
    clear_gateway_iam_auth_cache()
    yield
    clear_gateway_iam_auth_cache()


def test_is_iam_auth_active_follows_setting(settings):
    settings.BK_IAM_V4_ENABLED = False
    assert not is_iam_auth_active()

    settings.BK_IAM_V4_ENABLED = True
    assert is_iam_auth_active()


def test_is_iam_gateway_action_allowed_caches_only_allowed_results(settings, mocker):
    settings.BK_IAM_V4_ALLOW_CACHE_TTL = 60
    direct_auth = mocker.patch(
        "apigateway.biz.gateway.iam_auth.direct_auth",
        side_effect=[True, False, False],
    )

    assert is_iam_gateway_action_allowed("alice", 7, "manage_gateway")
    assert is_iam_gateway_action_allowed("alice", 7, "manage_gateway")
    assert not is_iam_gateway_action_allowed("bob", 7, "manage_gateway")
    assert not is_iam_gateway_action_allowed("bob", 7, "manage_gateway")

    assert direct_auth.call_count == 3
    direct_auth.assert_any_call(
        {
            "subject": {"type": "user", "id": "alice"},
            "action_id": "manage_gateway",
            "resource": {"id": "7"},
        }
    )


def test_is_iam_gateway_action_allowed_respects_zero_ttl(settings, mocker):
    settings.BK_IAM_V4_ALLOW_CACHE_TTL = 0
    direct_auth = mocker.patch("apigateway.biz.gateway.iam_auth.direct_auth", return_value=True)

    assert is_iam_gateway_action_allowed("alice", 7, "manage_gateway")
    assert is_iam_gateway_action_allowed("alice", 7, "manage_gateway")

    assert direct_auth.call_count == 2
