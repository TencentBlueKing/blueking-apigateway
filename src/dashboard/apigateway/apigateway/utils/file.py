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
from pathlib import Path


def read_file(path):
    with open(path, "rb") as fp:
        return fp.read()


def write_to_file(content, path, mode="w"):
    with open(path, mode) as fp:
        fp.write(content)


def iter_files_recursive(path: Path):
    """Iterate all files in a directory and its subdirectories"""

    for p in path.iterdir():
        if p.is_dir():
            yield from iter_files_recursive(p)
        else:
            yield p
