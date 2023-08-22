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
from django.utils.translation import gettext as _

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log


class GatewayLabelHandler:
    @staticmethod
    def record_audit_log_success(
        username: str,
        gateway_id: int,
        op_type: OpTypeEnum,
        instance_id: int,
        instance_name: str,
    ):
        comment = {
            OpTypeEnum.CREATE: _("创建网关标签"),
            OpTypeEnum.MODIFY: _("更新网关标签"),
            OpTypeEnum.DELETE: _("删除网关标签"),
        }.get(op_type, "-")

        record_audit_log(
            username=username,
            op_type=op_type.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=gateway_id,
            op_object_type=OpObjectTypeEnum.GATEWAY_LABEL.value,
            op_object_id=instance_id,
            op_object=instance_name,
            comment=comment,
        )
