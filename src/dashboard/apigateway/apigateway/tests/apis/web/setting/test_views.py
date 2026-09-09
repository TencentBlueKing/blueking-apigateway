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
import pytest

from apigateway.apis.web.setting.views import FeatureFlagListApi
from apigateway.tests.utils.testing import get_response_json


@pytest.mark.parametrize("edition", ["ee", "te"])
@pytest.mark.parametrize("tenant_mode", [False, True])
@pytest.mark.parametrize("docs_enabled", [False, True])
def test_esb_flags_cannot_restore_removed_features(
    settings, request_factory, mocker, edition, tenant_mode, docs_enabled
):
    settings.EDITION = edition
    settings.ENABLE_MULTI_TENANT_MODE = tenant_mode
    settings.DEFAULT_FEATURE_FLAG = {"MENU_ITEM_ESB_API_DOC": docs_enabled}
    mocker.patch(
        "apigateway.apis.web.setting.views.UserFeatureFlag.objects.get_feature_flags",
        return_value={
            "MENU_ITEM_ESB_API": True,
            "SYNC_ESB_TO_APIGW_ENABLED": True,
            "MENU_ITEM_ESB_API_DOC": docs_enabled,
        },
    )
    request = request_factory.get("")
    request.user = mocker.MagicMock(username="admin", is_superuser=True)
    data = get_response_json(FeatureFlagListApi.as_view()(request))["data"]
    assert "MENU_ITEM_ESB_API" not in data
    assert "SYNC_ESB_TO_APIGW_ENABLED" not in data
    assert data["MENU_ITEM_ESB_API_DOC"] is (edition == "te" and docs_enabled)
    assert settings.DEFAULT_FEATURE_FLAG["MENU_ITEM_ESB_API_DOC"] is docs_enabled
