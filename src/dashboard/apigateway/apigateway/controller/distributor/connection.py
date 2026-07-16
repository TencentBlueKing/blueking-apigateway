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
from typing import TYPE_CHECKING, Iterable, Tuple

from django.utils.translation import gettext as _

from apigateway.controller.distributor.etcd import GatewayResourceDistributor

if TYPE_CHECKING:
    from apigateway.apps.data_plane.models import DataPlane
    from apigateway.core.models import Release


def test_gateway_distributor_connection(release: "Release", data_plane: "DataPlane") -> Tuple[bool, str]:
    """检查网关发布对应数据面的 distributor 连接状态。"""
    distributor = GatewayResourceDistributor(release, data_plane=data_plane)
    ok, message = distributor.test_connection()
    if ok:
        return True, ""

    return False, _("数据面 {name} 连接失败：{message}").format(name=data_plane.name, message=message)


def test_gateway_distributor_connections(release: "Release", data_planes: Iterable["DataPlane"]) -> Tuple[bool, str]:
    """检查网关发布涉及的所有数据面连接状态。"""
    error_messages = []
    for data_plane in data_planes:
        ok, message = test_gateway_distributor_connection(release, data_plane)
        if not ok:
            error_messages.append(message)

    if error_messages:
        return False, "; ".join(error_messages)

    return True, ""
