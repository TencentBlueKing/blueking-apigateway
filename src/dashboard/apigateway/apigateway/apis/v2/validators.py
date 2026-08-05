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


def validate_output_fields(value: str, allowed_fields: Collection[str]) -> set[str] | None:
    fields = set(split_comma_separated_values(value, deduplicate=True))
    if not fields:
        return None

    unknown_fields = fields.difference(allowed_fields)
    if unknown_fields:
        raise serializers.ValidationError(_("不支持的字段：{fields}").format(fields=", ".join(sorted(unknown_fields))))
    return fields
