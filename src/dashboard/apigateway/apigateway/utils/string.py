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
import random
import string
import uuid


def truncate_string(s, length, suffix=""):
    """
    truncate string to specific length
    """
    if length >= len(s):
        return s
    if not suffix:
        return f"{s[:length]}"
    return f"{s[:length - len(suffix)]}{suffix}"


def random_string(length=10):
    """Generate a random string of fixed length"""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


def random_secret(length=10):
    """Generate a random secret of fixed length"""
    return "".join(random.choice(string.digits + string.ascii_letters + string.punctuation) for i in range(length))


def generate_unique_id():
    return uuid.uuid4().hex
