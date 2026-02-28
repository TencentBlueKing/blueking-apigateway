#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
import json
import logging
from typing import Any, ClassVar, Dict

from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway
from apigateway.utils.crypto import BkCrypto

from .constants import DataPlaneStatusEnum
from .managers import DataPlaneManager, GatewayDataPlaneBindingManager

logger = logging.getLogger(__name__)


class DataPlane(TimestampedModelMixin, OperatorModelMixin):
    """
    Data Plane represents a deployment environment with its own ETCD configuration.
    A gateway can be bound to multiple data planes.
    """

    name = models.CharField(max_length=32, unique=True, help_text=_("Data plane name"))
    description = models.CharField(max_length=512, blank=True, default="", help_text=_("Data plane description"))

    # Encrypted ETCD configuration as JSON
    # Structure: {"host": "...", "port": ..., "user": "...", "password": "...", ...}
    _encrypted_etcd_configs = models.TextField(
        db_column="encrypted_etcd_configs",
        blank=True,
        default="",
        help_text=_("Encrypted ETCD configuration in JSON format"),
    )

    # API URL template for this data plane
    bk_api_url_tmpl = models.CharField(max_length=512, blank=True, default="", help_text=_("API URL template"))

    status = models.IntegerField(
        choices=DataPlaneStatusEnum.get_choices(),
        default=DataPlaneStatusEnum.ACTIVE.value,
        help_text=_("Data plane status"),
    )

    is_recommend = models.BooleanField(default=False, help_text=_("Whether this is the recommended data plane"))

    objects: ClassVar[DataPlaneManager] = DataPlaneManager()

    def __str__(self):
        return f"<DataPlane: {self.pk}/{self.name}>"

    class Meta:
        verbose_name = _("DataPlane")
        verbose_name_plural = _("DataPlane")
        db_table = "data_plane"

    @property
    def etcd_configs(self) -> Dict[str, Any]:
        """Get decrypted ETCD configuration"""
        if not self._encrypted_etcd_configs:
            return {}
        try:
            crypto = BkCrypto()
            decrypted = crypto.decrypt(self._encrypted_etcd_configs)
            return json.loads(decrypted)
        except Exception:
            logger.exception("Failed to decrypt etcd_configs for data_plane %s", self.name)
            return {}

    @etcd_configs.setter
    def etcd_configs(self, value: Dict[str, Any]):
        """Set and encrypt ETCD configuration"""
        if not value:
            self._encrypted_etcd_configs = ""
            return
        try:
            crypto = BkCrypto()
            json_str = json.dumps(value, separators=(",", ":"))
            self._encrypted_etcd_configs = crypto.encrypt(json_str)
        except Exception:
            logger.exception("Failed to encrypt etcd_configs for data_plane %s", self.name)
            raise

    @property
    def is_active(self) -> bool:
        """Check if data plane is active"""
        return self.status == DataPlaneStatusEnum.ACTIVE.value


class GatewayDataPlaneBinding(TimestampedModelMixin, OperatorModelMixin):
    """
    Binding relationship between Gateway and DataPlane.
    A gateway can be bound to multiple data planes.
    """

    gateway = models.ForeignKey(
        Gateway,
        on_delete=models.CASCADE,
        related_name="data_plane_bindings",
        help_text=_("The gateway"),
    )
    data_plane = models.ForeignKey(
        DataPlane,
        on_delete=models.CASCADE,
        related_name="gateway_bindings",
        help_text=_("The data plane"),
    )

    objects: ClassVar[GatewayDataPlaneBindingManager] = GatewayDataPlaneBindingManager()

    def __str__(self):
        return f"<GatewayDataPlaneBinding: gateway={self.gateway_id}, data_plane={self.data_plane_id}>"

    class Meta:
        verbose_name = _("GatewayDataPlaneBinding")
        verbose_name_plural = _("GatewayDataPlaneBinding")
        db_table = "gateway_data_plane_binding"
        unique_together = ("gateway", "data_plane")
