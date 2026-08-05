# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.utils.string import split_comma_separated_values

if TYPE_CHECKING:
    from collections.abc import Collection

MAX_LOOKUP_NAMES = 50


def validate_comma_separated_names(
    value: str,
    *,
    max_count: int = MAX_LOOKUP_NAMES,
    max_count_error: str,
    required: bool = False,
    required_error: str | None = None,
) -> list[str]:
    names = split_comma_separated_values(value, deduplicate=True)
    if required and not names:
        raise serializers.ValidationError(required_error)
    if len(names) > max_count:
        raise serializers.ValidationError(max_count_error.format(max_count=max_count))
    return names


def validate_comma_separated_ints(
    value: str,
    *,
    max_count: int = MAX_LOOKUP_NAMES,
    max_count_error: str,
    invalid_error: str,
) -> list[int]:
    if not value:
        return []
    parts = split_comma_separated_values(value, deduplicate=False)
    try:
        ids = [int(part) for part in parts]
    except ValueError:
        raise serializers.ValidationError(invalid_error)
    if len(ids) > max_count:
        raise serializers.ValidationError(max_count_error.format(max_count=max_count))
    return ids


def validate_output_fields(value: str, allowed_fields: Collection[str]) -> set[str] | None:
    fields = set(split_comma_separated_values(value, deduplicate=True))
    if not fields:
        return None

    unknown_fields = fields.difference(allowed_fields)
    if unknown_fields:
        raise serializers.ValidationError(_("不支持的字段：{fields}").format(fields=", ".join(sorted(unknown_fields))))
    return fields
