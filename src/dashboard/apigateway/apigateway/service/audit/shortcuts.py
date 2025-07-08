# -*- coding: utf-8 -*-
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
import json

from django.core.serializers.json import DjangoJSONEncoder

from apigateway.apps.audit.signals import _record_audit_log_signal
from apigateway.utils.local import local
from apigateway.utils.string import truncate_string

AUDIT_SYSTEM = "apigateway-dashboard"


def record_audit_log(
    username,
    op_type,
    op_status,
    op_object_group,
    op_object_type,
    op_object_id=None,
    op_object=None,
    data_before=None,
    data_after=None,
    comment=None,
):
    data = {
        "event_id": local.request_id,
        "system": AUDIT_SYSTEM,
        "username": username,
        "op_type": op_type,
        "op_status": op_status,
        "op_object_group": op_object_group,
        "op_object_type": op_object_type,
        "comment": comment or "",
    }

    # 如果 op_object_id、op_object 过长，则截断
    if op_object_id:
        data["op_object_id"] = truncate_string(str(op_object_id), 64, suffix="...")
    if op_object:
        data["op_object"] = truncate_string(str(op_object), 512, suffix="...")

    # 如果 data_before, data_after 为非字符串，则 json.dumps
    if data_before is not None:
        data["data_before"] = (
            json.dumps(data_before, cls=DjangoJSONEncoder) if isinstance(data_before, (list, dict)) else data_before
        )
    if data_after is not None:
        data["data_after"] = (
            json.dumps(data_after, cls=DjangoJSONEncoder) if isinstance(data_after, (list, dict)) else data_after
        )

    _record_audit_log_signal.send(sender="system", **data)
