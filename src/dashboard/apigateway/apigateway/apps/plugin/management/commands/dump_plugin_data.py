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
import logging
import os
import sys
from typing import Any, List

from django.core import serializers
from django.core.management.base import BaseCommand
from django.core.serializers.pyyaml import DjangoSafeDumper
from django.db.models import Q

from apigateway.apps.plugin.models import PluginType
from apigateway.utils.yaml import multiline_str_presenter

logger = logging.getLogger(__name__)


DjangoSafeDumper.add_representer(str, multiline_str_presenter)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--include-private",
            action="store_true",
            default=False,
            help="include private plugin types",
        )
        parser.add_argument(
            "--allow-deletion",
            action="store_true",
            default=False,
            help="allow to delete the existing fixtures, if True, only dump plugins in database",
        )
        parser.add_argument(
            "--additional-plugin-types",
            nargs="+",
            default=[],
            help="additional plugin types to include, whatever there are private or public",
        )
        parser.add_argument("-f", "--fixture", required=True, help="fixture file path")

    def _iter_models(self, include_private: bool, additional_types: List[str]):
        qs = PluginType.objects.all().prefetch_related("schema").order_by("code")

        if not include_private:
            qs = qs.filter(Q(is_public=True) | Q(code__in=additional_types))

        for plugin_type in qs:
            # 以下模型的顺序要根据依赖顺序给出

            # 依赖的
            if plugin_type.schema:
                yield plugin_type.schema

            yield plugin_type

            # 被依赖的
            for form in plugin_type.pluginform_set.order_by("language"):
                yield form

    def _load_dumped_models(self, fixture: str, allow_deletion: bool):
        if not os.path.exists(fixture):
            raise ValueError(f"fixture file does not exist: {fixture}")

        with open(fixture, "rt") as fp:
            # ignorenonexistent=True: 模型中不存在序列化字段，忽略错误
            for m in serializers.deserialize("yaml", fp.read(), ignorenonexistent=True):
                # 反序列化会补全对象的 pk，pk 为 None 表示 fixture 中的对象在 db 中不存在；
                # 允许删除，即不处理 db 中不存在的（已删除的）对象
                if allow_deletion and m.object.pk is None:
                    continue

                yield m.object

    def _dump_models(self, fixture: str, models: List[Any]):
        with open(fixture, "wt") as fp:
            # 序列化时，将 model、fields 数据序列化为 yaml 格式，但不包含 pk/id 字段
            serializers.serialize(
                "yaml",
                models,
                indent=2,
                use_natural_foreign_keys=True,
                use_natural_primary_keys=True,
                stream=fp,
                progress_output=sys.stderr,
                object_count=len(models),
                allow_unicode=True,
            )

    def _update_additional_types(self, dumped_models: List[Any], additional_types: List[str]):
        for m in dumped_models:
            if not isinstance(m, PluginType):
                continue

            additional_types.append(m.code)

    def _merge_models(self, dumped: List[Any], newest: List[Any], allow_deletion: bool):
        # 允许删除，仅包含 db 中当前数据，不包含已删除的数据
        if allow_deletion:
            return newest

        merged = [i for i in newest]

        for m in dumped:
            if m.pk:
                continue

            merged.append(m)

        return merged

    def handle(
        self,
        include_private: bool,
        fixture: str,
        allow_deletion: bool,
        additional_plugin_types: List[str],
        **options,
    ):
        dumped = list(self._load_dumped_models(fixture, allow_deletion))

        self._update_additional_types(dumped, additional_plugin_types)

        newest = list(self._iter_models(include_private, additional_plugin_types))

        models = self._merge_models(dumped, newest, allow_deletion)

        self._dump_models(fixture, models)
