# -*- coding: utf-8 -*-
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

from django.conf import settings


def is_forbidden_host(host: str) -> bool:
    if ":" not in host:
        return False

    parts = host.split(":")

    port_str = parts[-1]
    if not port_str.isdigit():
        return True

    port_int = int(port_str)
    if port_int < 1 or port_int > 65535:
        return True

    if port_int in settings.FORBIDDEN_PORTS:
        return True

    return False
