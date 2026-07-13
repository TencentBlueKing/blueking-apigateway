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

"""Resource-version schema lookup and schema-version creation helpers."""

from typing import Set

from cachetools import TTLCache, cached
from django.utils.translation import gettext_lazy as _

from apigateway.apps.openapi.models import OpenAPIResourceSchema, OpenAPIResourceSchemaVersion
from apigateway.common.constants import CACHE_TIME_5_MINUTES
from apigateway.common.error_codes import error_codes
from apigateway.core.constants import ProxyTypeEnum, ResourceKindEnum
from apigateway.core.models import ResourceVersion
from apigateway.service.resource import get_resource_use_stage_vars


def get_resource_schema(resource_version_id: int, resource_id: int) -> dict:
    """获取资源版本中单个资源的 OpenAPI schema，用于资源详情、文档生成等场景。

    调用方同时持有 resource_version_id 和 resource_id，只需要一个资源的 schema 时使用。

    Args:
        resource_version_id (int): 资源版本 ID。
        resource_id (int): 资源 ID。

    Returns:
        dict: 命中的 OpenAPI schema；版本 schema 不存在或资源未命中时返回空字典。
    """
    resources_version_schema = OpenAPIResourceSchemaVersion.objects.filter(
        resource_version_id=resource_version_id
    ).first()
    if resources_version_schema is None:
        return {}

    # 筛选资源数据
    for schema_info in resources_version_schema.schema:
        if resource_id == schema_info["resource_id"]:
            return schema_info["schema"]

    return {}


def get_resource_id_to_schema_by_resource_version(resource_version_id: int) -> dict:
    """获取资源版本下所有资源的 OpenAPI schema 映射，用于批量读取 schema。

    资源版本展示、OpenAPI 导出、MCP 工具生成等场景需要按资源 ID 快速补全 schema 时使用。

    Args:
        resource_version_id (int): 资源版本 ID。

    Returns:
        dict: 键为资源 ID，值为对应 OpenAPI schema；版本 schema 不存在时返回空字典。
    """
    resources_version_schema = OpenAPIResourceSchemaVersion.objects.filter(
        resource_version_id=resource_version_id
    ).first()
    if resources_version_schema is None:
        return {}

    return {schema_info["resource_id"]: schema_info["schema"] for schema_info in resources_version_schema.schema}


@cached(cache=TTLCache(maxsize=300, ttl=CACHE_TIME_5_MINUTES))
def get_resource_names_set(resource_version_id: int, raise_exception: bool = False) -> Set[str]:
    """获取资源版本中的资源名称集合，用于权限、MCP Server 等名称存在性判断。

    频繁读取同一资源版本名称集合的路径使用；结果会缓存 5 分钟。

    Args:
        resource_version_id (int): 资源版本 ID。
        raise_exception (bool): 资源版本不存在时是否抛出 NOT_FOUND；为 False 时返回空集合。

    Returns:
        Set[str]: 资源名称集合；资源版本不存在且不抛异常时返回空集合。
    """
    resource_version = ResourceVersion.objects.filter(id=resource_version_id).first()
    if not resource_version:
        if raise_exception:
            raise error_codes.NOT_FOUND.format(_("资源版本不存在"))
        return set()

    return {resource["name"] for resource in resource_version.data}


# TODO: 缓存优化：可使用 django cache(with database backend) or dogpile 缓存
# 版本中包含的配置不会变化，但是处理逻辑可能调整，因此，缓存需支持版本
@cached(cache=TTLCache(maxsize=300, ttl=CACHE_TIME_5_MINUTES))
def get_used_stage_vars(gateway_id: int, resource_version_id: int):
    """获取资源版本中被资源引用的环境变量，用于发布校验时检查环境变量引用。

    校验指定网关、指定资源版本能否发布到某个环境时使用。

    Args:
        gateway_id (int): 网关 ID。
        resource_version_id (int): 资源版本 ID。

    Returns:
        dict | None: 存在资源版本时返回包含 in_path 和 in_host 的字典；资源版本不存在时返回 None。
    """
    resource_version = ResourceVersion.objects.filter(gateway_id=gateway_id, id=resource_version_id).first()
    if not resource_version:
        return None

    used_in_path = set()
    used_in_host = set()
    for resource in resource_version.data:
        if resource.get("kind", ResourceKindEnum.STANDARD.value) == ResourceKindEnum.AI.value:
            continue
        if resource["proxy"]["type"] != ProxyTypeEnum.HTTP.value:
            continue
        stage_vars = resource["stage_vars"] if resource.get("stage_vars") else get_resource_use_stage_vars(resource)
        used_in_path.update(stage_vars["in_path"])
        used_in_host.update(stage_vars["in_host"])
    return {
        "in_path": list(used_in_path),
        "in_host": list(used_in_host),
    }


def make_resource_schema_version(resource_version: ResourceVersion):
    """为资源版本创建 OpenAPI schema 快照，用于固化资源级 schema 的版本数据。

    创建 ResourceVersion 后立即调用；只有资源存在 schema 时才会创建版本 schema 记录。

    Args:
        resource_version (ResourceVersion): 已保存的资源版本实例，data 中应包含资源 ID。

    Returns:
        None: 有 schema 时写入 OpenAPIResourceSchemaVersion；没有 schema 时不创建记录。
    """
    resource_ids = [resource["id"] for resource in resource_version.data if "id" in resource]

    # 查询资源所有的schema
    resource_schemas = OpenAPIResourceSchema.objects.filter(resource_id__in=resource_ids)

    schema_list = [
        {
            "resource_id": resource_schema.resource.id,
            "schema": resource_schema.schema,
        }
        for resource_schema in resource_schemas
    ]
    if len(schema_list) > 0:
        OpenAPIResourceSchemaVersion.objects.create(
            resource_version=resource_version,
            schema=schema_list,
        )
