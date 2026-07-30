#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from ddf import G

from apigateway.apps.data_plane.constants import (
    CURRENT_DATA_PLANE_APISIX_VERSION,
    DEFAULT_DATA_PLANE_NAME,
    DataPlaneApisixVersionEnum,
)
from apigateway.apps.data_plane.management.commands.init_default_data_plane import Command
from apigateway.apps.data_plane.models import DataPlane

pytestmark = pytest.mark.django_db


def test_update_existing_default_data_plane_apisix_version(settings):
    settings.ETCD_CONFIG = {"host": "127.0.0.1", "port": 2379}
    settings.BK_API_URL_TMPL = "https://{api_name}.example.com"
    settings.BK_GATEWAY_ETCD_NAMESPACE_PREFIX = "/bk-gateway"

    default_data_plane = G(
        DataPlane,
        name=DEFAULT_DATA_PLANE_NAME,
        apisix_version=DataPlaneApisixVersionEnum.V3_13.value,
    )
    custom_data_plane = G(
        DataPlane,
        name="custom",
        apisix_version=DataPlaneApisixVersionEnum.V3_13.value,
    )

    Command().handle()

    default_data_plane.refresh_from_db()
    custom_data_plane.refresh_from_db()
    assert default_data_plane.apisix_version == CURRENT_DATA_PLANE_APISIX_VERSION
    assert custom_data_plane.apisix_version == DataPlaneApisixVersionEnum.V3_13.value
