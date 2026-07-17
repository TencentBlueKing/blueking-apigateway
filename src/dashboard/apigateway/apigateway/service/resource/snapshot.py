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

"""Resource snapshot construction and snapshot-related read helpers."""

import itertools
import json
import operator
from typing import TYPE_CHECKING, Dict, List, Optional

from django.conf import settings

from apigateway.apps.label.models import ResourceLabel
from apigateway.core.constants import STAGE_VAR_PATTERN, ContextScopeTypeEnum, ProxyTypeEnum, ResourceKindEnum
from apigateway.core.models import Context, Proxy, Resource, Stage, StageResourceDisabled
from apigateway.schema.models import Schema
from apigateway.utils import time

if TYPE_CHECKING:
    import datetime


def get_resource_id_to_proxy_snapshot(resource_ids: List[int]) -> Dict[int, Dict]:
    """批量生成资源代理配置快照，用于创建资源版本快照时批量组装 proxy 字段。

    调用方已经拿到资源 ID 列表，需要避免逐个资源查询 Proxy 时使用。

    Args:
        resource_ids (List[int]): 资源 ID 列表。

    Returns:
        Dict[int, Dict]: 键为资源 ID，值为该资源的代理配置快照；没有数据时返回空字典。
    """
    schemas = Schema.objects.filter_id_snapshot_map()
    return {
        proxy.resource_id: proxy.snapshot(as_dict=True, schemas=schemas)
        for proxy in Proxy.objects.filter(resource_id__in=resource_ids).prefetch_related("backend")
    }


def filter_disabled_stages_by_gateway(gateway):
    """查询网关下每个资源禁用的环境，用于创建资源快照时补全 disabled_stages 字段。

    需要按资源维度展示或保存“资源在哪些环境被禁用”的信息时使用。

    Args:
        gateway: 网关实例。

    Returns:
        dict: 键为资源 ID，值为禁用环境列表；每个环境包含 id 和 name。
    """
    stage_ids = Stage.objects.get_ids(gateway.id)

    queryset = StageResourceDisabled.objects.filter(stage_id__in=stage_ids)
    queryset = queryset.values("stage_id", "stage__name", "resource_id")

    disabled = sorted(queryset, key=operator.itemgetter("resource_id"))

    disabled_groups = itertools.groupby(disabled, key=operator.itemgetter("resource_id"))
    resource_disabled = {}
    for resource_id, group in disabled_groups:
        resource_disabled[resource_id] = [
            {
                "id": stage["stage_id"],
                "name": stage["stage__name"],
            }
            for stage in group
        ]
    return resource_disabled


def get_resource_use_stage_vars(resource: dict) -> dict:
    """解析资源代理配置中使用到的环境变量，用于发布校验时识别路径和 Host 变量引用。

    处理 ResourceVersion.data 中的资源快照，或兼容未保存 stage_vars 的旧快照时使用。

    Args:
        resource (dict): 资源快照字典，必须包含 proxy.config。

    Returns:
        dict: 包含 in_path 和 in_host 两个列表，分别表示路径变量和 Host 变量名称。
    """
    used_in_path = set()
    used_in_host = set()
    proxy_config = json.loads(resource["proxy"]["config"])
    proxy_path = proxy_config["path"]
    used_in_path.update(STAGE_VAR_PATTERN.findall(proxy_path))
    proxy_upstreams = proxy_config.get("upstreams")
    if proxy_upstreams:
        # 覆盖环境配置
        for host in proxy_upstreams["hosts"]:
            for match in STAGE_VAR_PATTERN.findall(host["host"]):
                used_in_host.add(match)
    return {
        "in_path": list(used_in_path),
        "in_host": list(used_in_host),
    }


def snapshot_resource(
    resource,
    as_dict=False,
    proxy_map=None,
    context_map=None,
    disabled_stage_map=None,
    api_label_map=None,
    plugin_map=None,
):
    """生成资源版本使用的单个资源快照，用于把编辑区 Resource 转换为 ResourceVersion.data 条目。

    创建资源版本或需要复用资源版本结构时调用；字段只能向后兼容新增，不能删除旧字段。

    Args:
        resource: Resource 实例。
        as_dict (bool): 是否直接返回字典；为 False 时返回 JSON 字符串。
        proxy_map: 可选的资源 ID 到代理快照映射，用于批量场景减少查询。
        context_map: 可选的资源 ID 到上下文快照映射。
        disabled_stage_map: 可选的资源 ID 到禁用环境名称列表映射。
        api_label_map: 可选的资源 ID 到标签 ID 列表映射。
        plugin_map: 可选的资源 ID 到插件配置快照列表映射。

    Returns:
        dict | str: as_dict 为 True 时返回快照字典，否则返回快照 JSON 字符串。
    """
    data = {
        "id": resource.pk,
        "kind": resource.kind,
        "name": resource.name,
        "description": resource.description,
        "description_en": resource.description_en,
        "method": resource.method,
        "path": resource.path,
        "match_subpath": resource.match_subpath,
        "enable_websocket": resource.enable_websocket,
        "is_public": resource.is_public,
        "allow_apply_permission": resource.allow_apply_permission,
        "created_time": time.format(resource.created_time),
        "updated_time": time.format(resource.updated_time),
    }

    if proxy_map is None:
        data["proxy"] = Proxy.objects.get(resource_id=resource.id).snapshot(as_dict=True)
    else:
        data["proxy"] = proxy_map[resource.id]

    # 资源使用的 stage vars
    if resource.kind == ResourceKindEnum.STANDARD.value and data["proxy"]["type"] == ProxyTypeEnum.HTTP.value:
        data["stage_vars"] = get_resource_use_stage_vars(data)

    if context_map is None:
        contexts = Context.objects.filter(
            scope_type=ContextScopeTypeEnum.RESOURCE.value,
            scope_id=resource.pk,
        ).all()
        data["contexts"] = {c.type: c.snapshot(as_dict=True) for c in contexts}
    else:
        data["contexts"] = context_map[resource.pk]

    if disabled_stage_map is None:
        data["disabled_stages"] = list(
            StageResourceDisabled.objects.filter(resource=resource).values_list("stage__name", flat=True)
        )
    else:
        data["disabled_stages"] = disabled_stage_map.get(resource.pk, [])

    if api_label_map is None:
        data["api_labels"] = list(
            ResourceLabel.objects.filter(resource_id=resource.pk).values_list("api_label_id", flat=True)
        )
    else:
        data["api_labels"] = api_label_map.get(resource.pk, [])

    if plugin_map:
        data["plugins"] = plugin_map.get(resource.pk, [])

    if as_dict:
        return data

    return json.dumps(data)


def get_last_resource_updated_time(gateway_id: int) -> Optional[datetime.datetime]:
    """获取网关下资源的最近更新时间，用于判断编辑区资源是否晚于最新资源版本。

    资源版本列表、发布前检查或任何需要比较资源与版本新旧的地方使用。

    Args:
        gateway_id (int): 网关 ID。

    Returns:
        Optional[datetime.datetime]: 最近更新时间；网关下没有资源时返回 None。
    """
    return (
        Resource.objects.filter(gateway_id=gateway_id)
        .order_by("-updated_time")
        .values_list("updated_time", flat=True)
        .first()
    )


def get_resource_updated_time(gateway_id: int, name: str) -> str:
    """获取网关下指定资源的格式化更新时间，用于 API 响应或资源文档展示。

    调用方用资源名称定位资源，并希望得到已经格式化的时间时使用。

    Args:
        gateway_id (int): 网关 ID。
        name (str): 资源名称。

    Returns:
        str: 格式化后的更新时间；资源不存在时返回空字符串。
    """
    resource = Resource.objects.filter(gateway_id=gateway_id, name=name).only("updated_time").first()
    if not resource:
        return ""
    return time.format(resource.updated_time)


def get_resource_url_tmpl() -> str:
    """获取资源访问地址模板，用于资源文档或展示逻辑读取统一的资源 URL 模板配置。

    调用方只需要读取 settings.API_RESOURCE_URL_TMPL，不应直接依赖 settings 时使用。

    Args:
        None: 此函数不接收输入参数。

    Returns:
        str: 资源访问地址模板。
    """
    return settings.API_RESOURCE_URL_TMPL
