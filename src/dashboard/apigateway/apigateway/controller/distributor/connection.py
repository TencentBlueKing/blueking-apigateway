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
import logging
from typing import TYPE_CHECKING

from apigateway.controller.distributor.base import DATA_PLANE_CONNECTION_CHECK_FAILED_MESSAGE
from apigateway.controller.distributor.etcd import GatewayResourceDistributor

if TYPE_CHECKING:
    from apigateway.apps.data_plane.models import DataPlane
    from apigateway.core.models import Release

logger = logging.getLogger(__name__)


class DistributorConnectionError(Exception):
    """Distributor 连接检查失败。"""


def check_gateway_distributor_connection(release: "Release", data_plane: "DataPlane") -> None:
    """检查网关发布对应数据面的 distributor 连接状态。"""
    try:
        distributor = GatewayResourceDistributor(release, data_plane=data_plane)
    except Exception as err:
        logger.warning(
            "init gateway distributor failed, data_plane_id=%s, data_plane_name=%s",
            data_plane.id,
            data_plane.name,
            exc_info=True,
        )
        raise DistributorConnectionError(
            DATA_PLANE_CONNECTION_CHECK_FAILED_MESSAGE.format(id=data_plane.id, name=data_plane.name)
        ) from err

    ok, message = distributor.test_connection()
    if ok:
        return

    raise DistributorConnectionError(message)
