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
from apigateway.apps.support.models import ReleasedResourceDoc
from apigateway.core.models import Release


def clear_unreleased_resource_doc(gateway_id: int) -> None:
    """清理不再被已发布版本引用的资源文档，用于发布成功后回收旧发布文档。

    资源版本发布完成并保存新的 ReleasedResourceDoc 后，调用此函数删除被新版本替代的旧文档。

    Args:
        gateway_id (int): 网关 ID，只清理该网关下的发布资源文档。

    Returns:
        None: 删除操作直接写数据库，不返回删除数量。
    """
    resource_version_ids = Release.objects.get_released_resource_version_ids(gateway_id)
    ReleasedResourceDoc.objects.filter(gateway_id=gateway_id).exclude(
        resource_version_id__in=resource_version_ids
    ).delete()
