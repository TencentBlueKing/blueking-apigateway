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
from enum import Enum

from common.errors import error_codes


class DataTypeEnum(Enum):
    OFFICIAL_PUBLIC = 1
    OFFICIAL_HIDDEN = 2
    CUSTOM = 3

    @property
    def is_official(self):
        return self._value_ in [self.OFFICIAL_PUBLIC.value, self.OFFICIAL_HIDDEN.value]


class LanguageEnum(Enum):
    EN = "en"
    ZH_HANS = "zh-hans"


class PermissionLevelEnum(Enum):
    UNLIMITED = "unlimited"
    NORMAL = "normal"
    SENSITIVE = "sensitive"
    SPECIAL = "special"


class LegacyPermissionLevel:
    _new_to_legacy_map = {
        PermissionLevelEnum.UNLIMITED.value: {
            "value": 0,
            "label": "无限制",
        },
        PermissionLevelEnum.NORMAL.value: {
            "value": 1,
            "label": "普通权限",
        },
        PermissionLevelEnum.SENSITIVE.value: {
            "value": 2,
            "label": "敏感权限",
        },
        PermissionLevelEnum.SPECIAL.value: {
            "value": 3,
            "label": "特殊权限",
        },
    }

    def __init__(self, value, label):
        self.value = value
        self.label = label

    @classmethod
    def from_new(cls, new_value: str):
        assert new_value in cls._new_to_legacy_map

        return cls(**cls._new_to_legacy_map[new_value])

    @classmethod
    def get_new(cls, legacy_value: int):
        for new_value, legacy_config in cls._new_to_legacy_map.items():
            if legacy_value == legacy_config["value"]:
                return PermissionLevelEnum(new_value)

        raise error_codes.ARGUMENT_ERROR.format_prompt(f"does not support permission level {legacy_value}")
