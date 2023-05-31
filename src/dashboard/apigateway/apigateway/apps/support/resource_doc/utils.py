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
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.resource_doc.constants import EN_RESOURCE_DOC_TMPL, ZH_RESOURCE_DOC_TMPL
from apigateway.core.models import Gateway, ReleasedResource


def get_resource_doc_tmpl(gateway_name: str, language: str) -> str:
    """获取资源文档模板"""
    # 将模板中的网关名替换为当前网关名（作为包名，将中折线替换为下划线）
    if language == DocLanguageEnum.ZH.value:
        template = ZH_RESOURCE_DOC_TMPL

    elif language == DocLanguageEnum.EN.value:
        template = EN_RESOURCE_DOC_TMPL

    else:
        template = ""

    return template.replace("__API_NAME__", gateway_name.replace("-", "_"))


def get_resource_doc_link(gateway: Gateway, resource_id: int) -> str:
    """获取资源文档链接"""
    if not gateway.is_active_and_public:
        return ""

    resource = ReleasedResource.objects.get_latest_released_resource(gateway.id, resource_id)
    if not resource or not resource["is_public"]:
        return ""

    return ReleasedResource.objects.get_latest_doc_link([resource_id]).get(resource_id, "")


def get_resource_doc_key(resource_id: int, language: str) -> str:
    return f"{resource_id}:{language}"
