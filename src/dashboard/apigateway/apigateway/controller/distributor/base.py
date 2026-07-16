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
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Tuple

from django.utils.translation import gettext as _

if TYPE_CHECKING:
    from apigateway.apps.data_plane.models import DataPlane

logger = logging.getLogger(__name__)

DATA_PLANE_CONNECTION_CHECK_FAILED_MESSAGE = _("数据面 ETCD 连接检查失败，请联系管理员。")


class BaseDistributor(ABC):
    data_plane: "DataPlane"
    _etcd_client: Any

    def test_connection(self) -> Tuple[bool, str]:
        """测试发布目标连接状态"""
        try:
            self._etcd_client.status()
        except Exception:  # pylint: disable=broad-except
            logger.warning(
                "test etcd connection failed, data_plane_id=%s, data_plane_name=%s",
                self.data_plane.id,
                self.data_plane.name,
                exc_info=True,
            )
            return False, DATA_PLANE_CONNECTION_CHECK_FAILED_MESSAGE

        return True, "ok"

    @abstractmethod
    def distribute(
        self,
        release_task_id: str,
        publish_id: int,
    ) -> Tuple[bool, str]:
        """发布到微网关"""
        raise NotImplementedError()

    @abstractmethod
    def revoke(
        self,
        release_task_id: str,
        publish_id: int,
    ) -> Tuple[bool, str]:
        """撤销微网关已发布内容"""
        raise NotImplementedError()
