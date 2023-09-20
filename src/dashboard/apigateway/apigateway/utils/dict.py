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
from typing import Any, Dict, Iterable, List, Optional, Type


def deep_update(mapping: Dict[str, Any], *updating_mappings: Dict[str, Any]) -> Dict[str, Any]:
    """
    参考：https://github.com/samuelcolvin/pydantic/blob/master/pydantic/utils.py#L174
    """
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping


def update_existing(mapping: Dict[str, Any], **update: Any) -> Dict[str, Any]:
    """
    更新 mapping 中已存在字段的值
    """
    updated_mapping = mapping.copy()
    updated_mapping.update({k: v for k, v in update.items() if k in updated_mapping})
    return updated_mapping


def get_item_by_path(item: Any, paths: Iterable[str], default=None) -> Any:
    """根据路径获取指定的值"""

    for path in paths:
        try:
            item = item[path]
        except (IndexError, KeyError):
            return default
        except Exception:
            raise

    return item


def set_item_by_path(item: Any, paths: List[str], value: Any, missing_type: Optional[Type] = None):
    """根据路径设置值"""
    if not paths:
        raise ValueError("No paths specified")

    if missing_type is None:
        missing_type = type(item)

    key = paths[-1]
    for path in paths[:-1]:
        try:
            item = item[path]
        except (IndexError, KeyError):
            # 当不存在时默认创建
            item[path] = missing_type()  # type: ignore
            item = item[path]
        except Exception:
            raise

    item[key] = value
