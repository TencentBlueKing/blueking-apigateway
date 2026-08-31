# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
import random
import string
import uuid


def split_comma_separated_values(
    value: str,
    *,
    strip: bool = True,
    deduplicate: bool = False,
    keep_empty: bool = False,
) -> list[str]:
    values = value.split(",")
    if strip:
        values = [item.strip() for item in values]
    if not keep_empty:
        values = [item for item in values if item]
    if deduplicate:
        values = list(dict.fromkeys(values))
    return values


def truncate_string(s, length, suffix=""):
    """
    truncate string to specific length
    """
    if length >= len(s):
        return s
    if not suffix:
        return f"{s[:length]}"
    return f"{s[: length - len(suffix)]}{suffix}"


def random_string(length=10):
    """Generate a random string of fixed length"""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


def generate_unique_id():
    return uuid.uuid4().hex


def strip_template_ref_prefix(value: object, prefix: str) -> str:
    value = str(value or "").strip()
    if value.startswith(prefix):
        return value[len(prefix) :]
    return value
