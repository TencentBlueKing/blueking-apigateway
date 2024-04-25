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
from blue_krill.data_types.enum import EnumField, StructuredEnum


# 资源导出 Swagger 配置中的扩展字段名
class OpenAPIExtensionEnum(StructuredEnum):
    METHOD_ANY = EnumField("x-bk-apigateway-method-any")
    RESOURCE = EnumField("x-bk-apigateway-resource")


# openAPI类型
class OpenAPITypeEnum(StructuredEnum):
    Swagger = EnumField("swagger")
    OpenAPI = EnumField("openapi")


VALID_METHOD_IN_SWAGGER_PATHITEM = [
    "get",
    "put",
    "post",
    "delete",
    "options",
    "head",
    "patch",
    OpenAPIExtensionEnum.METHOD_ANY.value,
]
