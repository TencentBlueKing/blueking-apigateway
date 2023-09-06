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
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from django.conf import settings
from django.utils.timezone import now as timezone_now


@dataclass
class SdkDocContext:
    gateway_name: str
    stage_name: str
    resource_name: str
    sdk_created_time: datetime = field(default_factory=timezone_now)
    gateway_name_with_underscore: str = ""
    django_settings: Any = settings

    def as_dict(self):
        return {
            "gateway_name": self.gateway_name,
            "gateway_name_with_underscore": self.gateway_name.replace("-", "_"),
            "stage_name": self.stage_name,
            "resource_name": self.resource_name,
            "sdk_created_time": self.sdk_created_time,
            "django_settings": self.django_settings,
        }


@dataclass
class DummySdkDocContext(SdkDocContext):
    gateway_name: str = "agent"
    stage_name: str = "prod"
    resource_name: str = "get_agent_status"
