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

from typing import List

from apigateway.apps.openapi.models import OpenAPIFileResourceSchemaVersion, OpenAPIResourceSchemaVersion
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.apps.support.models import ResourceDoc
from apigateway.core.constants import ContextScopeTypeEnum
from apigateway.core.models import Context, Proxy, Release, Resource, ResourceVersion


def delete_resources(resource_ids: List[int]):
    """删除指定资源及其强关联数据，用于集中清理认证配置、代理、插件绑定和资源文档。

    已明确拿到要删除的资源 ID 列表，需要保持资源相关表不残留脏数据时使用。

    Args:
        resource_ids (List[int]): 待删除资源 ID 列表；为空时不执行任何操作。

    Returns:
        None: 删除操作直接写数据库，不返回删除数量。
    """
    if not resource_ids:
        return

    # 1. delete auth config context
    Context.objects.filter(scope_type=ContextScopeTypeEnum.RESOURCE.value, scope_id__in=resource_ids).delete()

    # 2. delete proxy
    Proxy.objects.filter(resource_id__in=resource_ids).delete()

    # 3. delete plugin binding
    PluginBinding.objects.filter(
        scope_type=PluginBindingScopeEnum.RESOURCE.value,
        scope_id__in=resource_ids,
    ).delete()

    # 4. delete resource doc
    ResourceDoc.objects.filter(resource_id__in=resource_ids).delete()

    # 5. delete resource
    Resource.objects.filter(id__in=resource_ids).delete()


def delete_gateway_resources(gateway_id: int):
    """删除网关下全部资源及资源强关联数据，用于网关删除或网关资源全量重置。

    调用方只知道网关 ID，需要清理该网关当前所有资源时使用。

    Args:
        gateway_id (int): 网关 ID。

    Returns:
        None: 删除操作直接写数据库，不返回删除数量。
    """
    resource_ids = list(Resource.objects.filter(gateway_id=gateway_id).values_list("id", flat=True))
    delete_resources(resource_ids)


def delete_gateway_resource_versions(gateway_id: int):
    """删除网关下全部资源版本及发布产物，用于网关删除或资源版本全量重置。

    需要清除一个网关所有已生成的版本与发布引用，再由上层决定是否继续删除资源本体时使用。

    Args:
        gateway_id (int): 网关 ID。

    Returns:
        None: 删除操作直接写数据库，不返回删除数量。
    """
    # delete gateway release
    Release.objects.filter(gateway_id=gateway_id).delete()

    # delete gateway openapi resource schema version
    OpenAPIResourceSchemaVersion.objects.filter(resource_version__gateway_id=gateway_id).delete()

    # delete gateway openapi file resource schema version
    OpenAPIFileResourceSchemaVersion.objects.filter(gateway_id=gateway_id).delete()

    # delete resource version
    ResourceVersion.objects.filter(gateway_id=gateway_id).delete()
