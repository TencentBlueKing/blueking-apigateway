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
from collections import OrderedDict
from enum import Enum

import ruamel
from ruamel.yaml import YAML, Dumper
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


def yaml_load_all(content):
    return _yaml.load_all(content)


def yaml_dumps(data):
    """
    avoid-omap-ruamel
    - https://gist.github.com/monester/3f3bd87a936d1017c1f5089650b79a98
    """
    stream = StringIO()
    _yaml.dump(data, stream=stream)
    return stream.getvalue()


def yaml_dumps_multiline_string(data):
    return ruamel.yaml.dump(data, default_style="|")


class YamlRepresenterHookMixin:
    """This mixin is used to add a representer hook to the yaml dumper."""

    def __init_subclass__(cls, **kwargs):
        _yaml.representer.add_representer(cls, cls.yaml_representer)

    @classmethod
    def yaml_representer(cls, dumper: Dumper, data):
        """This method is used to represent the data in the yaml, work for yaml_dumps."""

        raise NotImplementedError


class YamlRepresenterEnum(YamlRepresenterHookMixin, Enum):
    """This class is bound to the enum class, and used to represent the enum in the yaml."""

    def __reduce_ex__(self, proto):
        # this method is used to help the pickle library to handle the enum classes under python3.6
        return self.name

    @classmethod
    def yaml_representer(cls, dumper: Dumper, data):
        data_type = type(data.value)
        representer_name = f"represent_{data_type.__name__}"
        representer = getattr(dumper, representer_name, None)
        if not representer:
            raise NotImplementedError(representer_name)

        return representer(data.value)


def multiline_str_presenter(dumper, data):
    text_list = [line.rstrip() for line in data.splitlines()]
    fix_data = "\n".join(text_list)
    if len(text_list) > 1:
        return dumper.represent_scalar("tag:yaml.org,2002:str", fix_data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", fix_data)
