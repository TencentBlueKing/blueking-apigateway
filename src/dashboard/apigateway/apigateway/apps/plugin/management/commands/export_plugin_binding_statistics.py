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
import csv
from typing import Any, Dict, List, Optional

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext as _

from apigateway.apps.plugin.models import PluginBinding, PluginType
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway, Resource


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--plugin-name",
            type=str,
            required=True,
            help="插件名称",
        )

        parser.add_argument(
            "--only-active-gateway",
            action="store_true",
            help="是否只统计已启用的网关",
        )

        parser.add_argument(
            "--show-gateway-list",
            action="store_true",
            help="展示绑定网关列表",
        )

        parser.add_argument(
            "--show-resource-list",
            action="store_true",
            help="展示资源列表",
        )

    def _build_plugin_section(self, plugin_name: str, plugin_bindings) -> Dict[str, Any]:
        bind_gateway_count = plugin_bindings.values_list("gateway", flat=True).distinct().count()
        bind_resource_count = plugin_bindings.values_list("scope_id", flat=True).distinct().count()

        return {
            "title": "插件统计",
            "headers": ["plugin_name", "gateway_count", "resource_count"],
            "header_row": {
                "plugin_name": _("插件名称"),
                "gateway_count": _("绑定网关数量"),
                "resource_count": _("绑定资源数量"),
            },
            "data": [
                {
                    "plugin_name": plugin_name,
                    "gateway_count": bind_gateway_count,
                    "resource_count": bind_resource_count,
                }
            ],
        }

    def _build_gateway_list_section(self, plugin_bindings) -> Optional[Dict[str, Any]]:
        gateway_ids = plugin_bindings.values_list("gateway_id", flat=True).distinct()
        gateways = Gateway.objects.filter(id__in=gateway_ids)

        gateway_data = [
            {
                "gateway_id": gateway.id,
                "gateway_name": gateway.name,
                "gateway_desc": gateway.description or "",
                "gateway_maintainers": gateway._maintainers or "",
                "gateway_status": "启用" if gateway.is_active else "停用",
            }
            for gateway in gateways
        ]

        if not gateway_data:
            return None

        return {
            "title": "绑定网关列表",
            "sheet_name": "网关列表",
            "headers": ["gateway_id", "gateway_name", "gateway_desc", "gateway_maintainers", "gateway_status"],
            "header_row": {
                "gateway_id": _("网关ID"),
                "gateway_name": _("网关名称"),
                "gateway_desc": _("网关描述"),
                "gateway_maintainers": _("网关负责人"),
                "gateway_status": _("网关状态"),
            },
            "data": gateway_data,
        }

    def _build_resource_list_section(self, plugin_bindings) -> Optional[Dict[str, Any]]:
        # 资源ID到插件配置ID的映射
        resource_config_map = {b["scope_id"]: b["config_id"] for b in plugin_bindings.values("scope_id", "config_id")}
        resources = Resource.objects.filter(id__in=resource_config_map.keys())

        resource_data = [
            {
                "resource_id": resource.id,
                "resource_name": resource.name,
                "plugin_config_id": resource_config_map[resource.id],
            }
            for resource in resources
        ]

        if not resource_data:
            return None

        return {
            "title": "绑定资源列表",
            "sheet_name": "资源列表",
            "headers": ["resource_id", "resource_name", "plugin_config_id"],
            "header_row": {
                "resource_id": _("资源ID"),
                "resource_name": _("资源名称"),
                "plugin_config_id": _("插件配置ID"),
            },
            "data": resource_data,
        }

    def _export_to_csv(self, sections: List[Dict[str, Any]], filename: str):
        with open(filename, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)

            total_rows = 0
            for idx, section in enumerate(sections):
                # 写入段标题（作为注释行）
                title = section.get("title", "")
                if title:
                    writer.writerow([f"# {title}"])

                headers = section["headers"]
                header_row = section["header_row"]
                data = section["data"]

                # 写入表头（中文）
                header_values = [header_row.get(h, h) for h in headers]
                writer.writerow(header_values)

                # 写入数据行
                for row_data in data:
                    row_values = [row_data.get(h, "") for h in headers]
                    writer.writerow(row_values)
                    total_rows += 1

                # 在段之间添加空行（最后一段除外）
                if idx < len(sections) - 1:
                    writer.writerow([])
                    writer.writerow([])

        self.stdout.write(self.style.SUCCESS(f"已导出到 {filename}"))

    def handle(self, *args, **options):
        plugin_name = options["plugin_name"]
        only_active_gateway = options["only_active_gateway"]
        show_gateway_list = options["show_gateway_list"]
        show_resource_list = options["show_resource_list"]

        try:
            plugin_type = PluginType.objects.get(code=plugin_name)
        except PluginType.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"插件类型 '{plugin_name}' 不存在"))
            return

        plugin_queryset = PluginBinding.objects.filter(config__type=plugin_type)
        if not plugin_queryset.exists():
            self.stderr.write(self.style.WARNING(f"插件类型 '{plugin_type.name}' 暂未被使用"))
            return

        if only_active_gateway:
            plugin_queryset = plugin_queryset.filter(gateway__status=GatewayStatusEnum.ACTIVE.value)
            if not plugin_queryset.exists():
                self.stderr.write(self.style.WARNING(f"插件类型 '{plugin_type.name}' 在已启用网关中暂未被使用"))
                return

        sections = [
            # 构建插件统计数据
            self._build_plugin_section(plugin_name, plugin_queryset)
        ]

        # 构建绑定网关列表数据
        if show_gateway_list:
            gateway_section = self._build_gateway_list_section(plugin_queryset)
            if gateway_section:
                sections.append(gateway_section)

        # 构建绑定资源列表数据
        if show_resource_list:
            resource_section = self._build_resource_list_section(plugin_queryset)
            if resource_section:
                sections.append(resource_section)

        now = timezone.now().strftime("%Y%m%d%H%M%S")
        filename = f"plugin_usage_{plugin_name}_{now}.csv"
        self._export_to_csv(sections, filename)
