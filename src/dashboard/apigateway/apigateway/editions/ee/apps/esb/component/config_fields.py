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
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, TypeAdapter


class FieldTypeEnum(str, Enum):
    string = "string"
    boolean = "boolean"
    int = "int"
    enum = "enum"
    password = "password"


class ConfigField(BaseModel):
    """
    参考：https://www.rancher.co.jp/docs/rancher/v2.x/en/catalog/custom/creating/#question-variable-reference
    """

    variable: str
    label: str
    type: FieldTypeEnum = FieldTypeEnum.string
    default: Any = ""
    options: Optional[list] = None
    show_if: Optional[str] = None


def enrich_config_fields(config_fields: List[dict], config: Dict[str, Any]) -> List[dict]:
    for field in config_fields:
        field.update(
            {
                "label": field.get("label") or field["variable"],
                "default": config.get(field["variable"], field.get("default", "")),
            }
        )

    return [field.dict(exclude_none=True) for field in TypeAdapter(List[ConfigField]).validate_python(config_fields)]
