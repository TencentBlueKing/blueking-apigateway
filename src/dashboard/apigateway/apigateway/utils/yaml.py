# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
import re
from collections import OrderedDict

from ruamel.yaml import YAML
from ruamel.yaml import resolver as yaml_resolver
from ruamel.yaml.compat import StringIO


def _mapping_representer(dumper, data):
    """用于处理字典延伸类型的数据"""
    return dumper.represent_mapping(yaml_resolver.BaseResolver.DEFAULT_MAPPING_TAG, data)


_yaml = YAML()
_yaml.width = 10000  # 超过这个宽度会折行，这个特性会在渲染 Chart 的时候导致模板报错，必须设置很大的值
_yaml.representer.add_representer(OrderedDict, _mapping_representer)


# https://yaml.org/type/bool.html
_yaml_10_boolean_values = {
    "y",
    "Y",
    "yes",
    "Yes",
    "YES",
    "n",
    "N",
    "no",
    "No",
    "NO",
    "true",
    "True",
    "TRUE",
    "false",
    "False",
    "FALSE",
    "on",
    "On",
    "ON",
    "off",
    "Off",
    "OFF",
}


def _force_quoted_string_representer(dumper, data):
    """
    Yaml specification (<1.2) treats the literal 'y' as a boolean value,
    but in newest version, 'y' become a normal string.
    So we quotes the string to eliminate this difference.
    """
    node = dumper.represent_str(data)

    if data in _yaml_10_boolean_values:
        node.style = "'"

    return node


_yaml.representer.add_representer(str, _force_quoted_string_representer)


def yaml_loads(content):
    return _yaml.load(content)


def _multiline_string_representer(dumper, data):
    node = dumper.represent_str(data)

    if data in _yaml_10_boolean_values:
        node.style = "'"
        return node

    if "\n" in data:
        # 以 "|" 格式输出 yaml 字符串
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return node


def yaml_export_dumps(data):
    export_yaml = YAML()
    export_yaml.width = 10000  # 超过这个宽度会折行，这个特性会在渲染 Chart 的时候导致模板报错，必须设置很大的值
    export_yaml.representer.add_representer(OrderedDict, _mapping_representer)
    export_yaml.representer.add_representer(str, _multiline_string_representer)
    stream = StringIO()
    export_yaml.dump(data, stream=stream)
    return stream.getvalue()


# def yaml_load_all(content):
#     return _yaml.load_all(content)


def yaml_dumps(data):
    """
    avoid-omap-ruamel
    - https://gist.github.com/monester/3f3bd87a936d1017c1f5089650b79a98
    """
    stream = StringIO()
    _yaml.dump(data, stream=stream)
    return stream.getvalue()


# def yaml_dumps_multiline_string(data):
#     return ruamel.yaml.dump(data, default_style="|")


def multiline_str_presenter(dumper, data):
    text_list = [line.rstrip() for line in data.splitlines()]
    fix_data = "\n".join(text_list)
    if len(text_list) > 1:
        return dumper.represent_scalar("tag:yaml.org,2002:str", fix_data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", fix_data)


# 匹配 \uXXXX 和 \UXXXXXXXX 格式的 Unicode 转义序列
_UNICODE_ESCAPE_RE = re.compile(r"\\u([0-9a-fA-F]{4})|\\U([0-9a-fA-F]{8})")


def _replace_unicode_escape(match: re.Match) -> str:
    """将匹配到的 \\uXXXX 或 \\UXXXXXXXX 转换为对应的 Unicode 字符"""
    if match.group(1):
        return chr(int(match.group(1), 16))
    return chr(int(match.group(2), 16))


def decode_unicode_escape_safe(s: str) -> str:
    """安全的 Unicode 转义解码。

    仅处理 \\uXXXX 和 \\UXXXXXXXX 格式的 Unicode 转义序列，
    不会影响其他反斜杠转义（如 \\" \\n \\\\ 等），避免破坏 YAML 嵌套字符串的引号结构。

    这是 `str.encode().decode("unicode_escape")` 的安全替代：
    - unicode_escape 会将 \\" 转为 "，导致内层 YAML 解析失败
    - 本函数只转换 Unicode 码点转义，保留其他转义序列不变
    """
    return _UNICODE_ESCAPE_RE.sub(_replace_unicode_escape, s)
