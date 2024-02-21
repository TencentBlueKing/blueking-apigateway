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

import os
import re
from enum import Enum
from typing import Dict, List

from django.conf import settings
from django.utils import translation

MD_FILE_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
MD_FILE_VERSION_PATTERN = re.compile(r"[vV]\d+\.\d+\.\d+")


class DjangoLanguageEnum(Enum):
    ZH_HANS = "zh-hans"
    EN = "en"


def _get_change_log_file_name() -> str:
    """获取日志文件名称"""
    if translation.get_language() == DjangoLanguageEnum.EN.value:
        return "CHANGELOG_en.md"
    return "CHANGELOG.md"


def _read_file_content(file_path: str) -> str:
    """读取文件内容"""
    content = ""
    if os.path.isfile(file_path):
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    return content


def get_version_list() -> List[Dict[str, str]]:
    """
    获取 md 日志版本列表
    :return {版本号，日期，文件内容} 字段列表，列表根据版本号从大到小排列
    """
    file_dir = settings.VERSION_LOG_DIR
    if not os.path.isdir(file_dir):  # md 文件夹不存在
        return []

    file_name = _get_change_log_file_name()
    if not os.path.isfile(os.path.join(file_dir, file_name)):
        return []

    text = _read_file_content(os.path.join(file_dir, file_name))

    data = []
    for log in text.split("---"):
        try:
            parts = log.strip().split("\n")

            date = MD_FILE_DATE_PATTERN.findall(parts[0])[0]  # 从第一行提取日期
            version = MD_FILE_VERSION_PATTERN.findall(parts[1])[0]  # 从第二行提取版本号

            content = "\n".join(parts[1:])  # 去除日期注释，重新组合

            data.append({"version": version, "date": date, "content": content})
        except Exception:  # pylint: disable=broad-except
            pass

    return data
