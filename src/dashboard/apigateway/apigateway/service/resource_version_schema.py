from typing import Set

from cachetools import TTLCache, cached
from django.utils.translation import gettext_lazy as _

from apigateway.apps.openapi.models import OpenAPIResourceSchemaVersion
from apigateway.common.constants import CACHE_TIME_5_MINUTES
from apigateway.common.error_codes import error_codes
from apigateway.core.constants import ProxyTypeEnum
from apigateway.core.models import ResourceVersion
from apigateway.service.resource_snapshot import get_resource_use_stage_vars


def get_resource_schema(resource_version_id: int, resource_id: int) -> dict:
    """
    获取指定版本的资源对应的api schema
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
    """
    获取资源版本下的资源与 api schema 的映射关系
    """
    resources_version_schema = OpenAPIResourceSchemaVersion.objects.filter(
        resource_version_id=resource_version_id
    ).first()
    if resources_version_schema is None:
        return {}

    return {schema_info["resource_id"]: schema_info["schema"] for schema_info in resources_version_schema.schema}


def get_resource_names_set(resource_version_id: int, raise_exception: bool = False) -> Set[str]:
    """获取资源版本中的资源名称列表, 缓存 5 分钟

    Args:
        resource_version_id (int): 资源版本 ID
        raise_exception (bool, optional): 是否抛出异常, 如果资源版本不存在, 则抛出异常. 默认 False
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
    resource_version = ResourceVersion.objects.filter(gateway_id=gateway_id, id=resource_version_id).first()
    if not resource_version:
        return None

    used_in_path = set()
    used_in_host = set()
    for resource in resource_version.data:
        if resource["proxy"]["type"] != ProxyTypeEnum.HTTP.value:
            continue
        stage_vars = resource["stage_vars"] if resource.get("stage_vars") else get_resource_use_stage_vars(resource)
        used_in_path.update(stage_vars["in_path"])
        used_in_host.update(stage_vars["in_host"])
    return {
        "in_path": list(used_in_path),
        "in_host": list(used_in_host),
    }
