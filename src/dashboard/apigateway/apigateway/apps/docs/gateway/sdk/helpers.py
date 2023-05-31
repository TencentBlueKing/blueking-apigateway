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
import json
from abc import ABCMeta
from collections import OrderedDict
from dataclasses import InitVar, dataclass, field
from datetime import datetime
from typing import Any

from dateutil import parser as dateutil_parser
from django.conf import settings
from django.utils.timezone import now as timezone_now

from apigateway.apps.docs.gateway.constants import RE_PATH_VARIABLE
from apigateway.apps.docs.helper import support_helper


@dataclass
class ResourceForSDK(metaclass=ABCMeta):
    api_id: int
    api_name: str
    stage_name: str
    resource_name: str
    path_params: str = ""
    api_name_with_underscore: str = ""
    sdk_created_time: datetime = field(default_factory=timezone_now)
    django_settings: Any = settings
    sdk_created_time_str: InitVar[str] = ""

    def __post_init__(self, sdk_created_time_str):
        self.api_name_with_underscore = self.api_name.replace("-", "_")

        if sdk_created_time_str:
            self.sdk_created_time = dateutil_parser.parse(sdk_created_time_str)

    def as_dict(self):
        # return asdict(self)
        return {
            "api_id": self.api_id,
            "api_name": self.api_name,
            "stage_name": self.stage_name,
            "resource_name": self.resource_name,
            "path_params": self.path_params,
            "api_name_with_underscore": self.api_name_with_underscore,
            "sdk_created_time": self.sdk_created_time,
            "django_settings": self.django_settings,
        }


@dataclass
class ReleasedResourceForSDK(ResourceForSDK):
    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)

        released_resource = support_helper.get_released_resource(
            self.api_id,
            self.stage_name,
            self.resource_name,
        )
        self.path_params = self._get_path_params(released_resource.get("path"))

    def _get_path_params(self, path: str) -> str:
        if not path:
            return ""

        path_var_fields = RE_PATH_VARIABLE.findall(path)
        if not path_var_fields:
            return ""

        return json.dumps(OrderedDict([(key, "1") for key in path_var_fields]))


@dataclass
class DummyResourceForSDK(ResourceForSDK):
    api_id: int = -1
    api_name: str = "agent"
    stage_name: str = "prod"
    resource_name: str = "get_agent_status"
    path_params: str = json.dumps({"bk_biz_id": 123})
