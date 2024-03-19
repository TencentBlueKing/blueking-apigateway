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
"""
网关认证配置管理
"""

import copy
from typing import List, Optional

from django.conf import settings
from pydantic import BaseModel, Field

from apigateway.core.constants import GatewayTypeEnum
from apigateway.utils.dict import update_existing


class UserAuthConfig(BaseModel):
    """
    网关用户认证配置
    """

    user_auth_type: str
    rtx_conf: dict = Field(default_factory=dict)
    uin_conf: dict = Field(default_factory=dict)
    # 开源版 default 类型用户的配置
    user_conf: dict = Field(default_factory=dict)

    @property
    def config(self) -> dict:
        user_config_key = self._get_user_config_key()
        current_user_config = getattr(self, user_config_key, {})
        # 因 uin_conf/rtx_conf/user_conf 包含不同的配置字段，因此，合并时，仅取当前配置已有的字段
        user_config = update_existing(self._get_default_user_config(), **current_user_config)

        return {
            user_config_key: user_config,
        }

    def _get_user_config_key(self):
        # 因 apigw-ng 使用 user_type 是否为空判断用户类型，因此，此处使用 user_type 与 key 映射
        user_type_to_key_map = {
            "rtx": "rtx_conf",
            "uin": "uin_conf",
            "default": "user_conf",
        }
        user_type = settings.API_USER_AUTH_CONFIGS[self.user_auth_type]["user_type"]
        return user_type_to_key_map[user_type]

    def _get_default_user_config(self) -> dict:
        # 为防止 settings 被修改，返回 deepcopy 数据
        return copy.deepcopy(settings.API_USER_AUTH_CONFIGS[self.user_auth_type])


class APIAuthConfig(BaseModel):
    """
    网关认证配置
    """

    user_auth_type: str
    api_type: int = GatewayTypeEnum.CLOUDS_API.value
    unfiltered_sensitive_keys: List[str] = Field(default_factory=list)
    allow_update_api_auth: bool = getattr(settings, "DEFAULT_ALLOW_UPDATE_API_AUTH", False)
    allow_auth_from_params: Optional[bool] = None
    allow_delete_sensitive_params: Optional[bool] = None
    include_system_headers: Optional[List[str]] = None
    rtx_conf: dict = Field(default_factory=dict)
    uin_conf: dict = Field(default_factory=dict)
    user_conf: dict = Field(default_factory=dict)

    @property
    def config(self) -> dict:
        config = {
            "user_auth_type": self.user_auth_type,
            "api_type": self.api_type,
            "allow_update_api_auth": self.allow_update_api_auth,
            "unfiltered_sensitive_keys": self.unfiltered_sensitive_keys,
        }

        if self.include_system_headers:
            config["include_system_headers"] = self.include_system_headers

        if self.allow_auth_from_params is not None:
            config["allow_auth_from_params"] = self.allow_auth_from_params

        if self.allow_delete_sensitive_params is not None:
            config["allow_delete_sensitive_params"] = self.allow_delete_sensitive_params

        # 更新用户认证配置
        config.update(
            UserAuthConfig(
                user_auth_type=self.user_auth_type,
                rtx_conf=self.rtx_conf,
                uin_conf=self.uin_conf,
                user_conf=self.user_conf,
            ).config
        )

        return config
