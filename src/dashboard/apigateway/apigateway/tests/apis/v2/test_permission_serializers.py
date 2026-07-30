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
from rest_framework.exceptions import ValidationError

from apigateway.apis.v2.inner import serializers as inner_serializers
from apigateway.apis.v2.open import serializers as open_serializers
from apigateway.apis.v2.sync import serializers as sync_serializers


@pytest.mark.parametrize("app_code", ["public", "personal"])
@pytest.mark.parametrize(
    "serializer_class",
    [
        open_serializers.GatewayAppPermissionApplyInputSLZ,
        inner_serializers.GatewayAppPermissionApplyCreateInputSLZ,
        inner_serializers.AppPermissionRenewInputSLZ,
        sync_serializers.GatewayAppPermissionGrantInputSLZ,
    ],
)
def test_mutation_serializer_rejects_oauth2_builtin_app_code(serializer_class, app_code):
    field = serializer_class().fields["target_app_code"]

    with pytest.raises(ValidationError):
        field.run_validation(app_code)


@pytest.mark.parametrize("app_code", ["public", "personal"])
def test_mcp_permission_serializer_allows_oauth2_builtin_app_code(app_code):
    field = open_serializers.MCPServerAppPermissionApplyCreateInputSLZ().fields["bk_app_code"]

    assert field.run_validation(app_code) == app_code
