#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the MIT License (the "License"); you may not use this file except
#  in compliance with the License. You may obtain a copy of the License at
#  #
#      http://opensource.org/licenses/MIT
#  #
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
#  either express or implied. See the License for the specific language governing permissions and
#  limitations under the License.
#  #
#  We undertake not to change the open source license (MIT license) applicable
#  to the current version of the project delivered to anyone in the future.
#  #
from functools import partial
from importlib.resources import as_file, files
from os import path
from typing import Any, Hashable, List, Mapping, Tuple

from jsonschema.validators import Draft4Validator, Draft202012Validator
from jsonschema_path.readers import FilePathReader
from lazy_object_proxy import Proxy
from openapi_spec_validator import versions
from openapi_spec_validator.shortcuts import SPEC2VALIDATOR
from openapi_spec_validator.validation import (
    SpecValidatorProxy,
    openapi_v2_spec_validator,
    openapi_v30_spec_validator,
    openapi_v31_spec_validator,
)
from openapi_spec_validator.versions.datatypes import SpecVersion

openapi_validator_mapping: Mapping[SpecVersion, SpecValidatorProxy] = {
    versions.OPENAPIV2: openapi_v2_spec_validator,
    versions.OPENAPIV30: openapi_v30_spec_validator,
    versions.OPENAPIV31: openapi_v31_spec_validator,
}


def _load_open_schema_for_apigw(version: str) -> Tuple[Mapping[Hashable, Any], str]:
    """
    根据不同版本加载不同版本的 schema
    """
    schema_path = f"schemas/openapi_{version}_schema.json"
    ref = files("apigateway.biz.resource.importer") / schema_path
    with as_file(ref) as resource_path:
        schema_path_full = path.join(path.dirname(__file__), resource_path)
    return FilePathReader(schema_path_full).read()


def _get_apigw_schema_content(spec_version: SpecVersion) -> Mapping[Hashable, Any]:
    """
    加载不同版本 schema 内容
    """
    content, _ = _load_open_schema_for_apigw(f"{spec_version.major}.{spec_version.minor}")
    return content


def get_apigw_schema_validator(spec_version: SpecVersion) -> SpecValidatorProxy:
    """
    根据版本获取不同的 spec_validator
    """
    spec_validator = SPEC2VALIDATOR[spec_version]

    get_apigw_schema_content = Proxy(partial(_get_apigw_schema_content, spec_version))

    # 修改一下spec_validator的 schema_validator
    if spec_version == versions.OPENAPIV31:
        spec_validator.schema_validator = Proxy(partial(Draft202012Validator, get_apigw_schema_content))
    else:
        spec_validator.schema_validator = Proxy(partial(Draft4Validator, get_apigw_schema_content))

    return openapi_validator_mapping[spec_version]


def set_openapi_parser_schema_validator(spec_version: SpecVersion):
    """
    设置openai转换器使用的schema_validator
    """
    get_apigw_schema_content = Proxy(partial(_get_apigw_schema_content, spec_version))

    SPEC2VALIDATOR[spec_version].schema_validator = Proxy(partial(Draft4Validator, get_apigw_schema_content))


class SchemaValidateErr:
    """验证schema错误的类"""

    def __init__(self, message: str, json_path: str, absolute_path: List[str]):
        """初始化新的SchemaValidationError对象。

        参数:
            message (str): 错误描述。
            json_path (str): 指示错误位置的JSON路径表达式。
            absolute_path (List[str]): 错误的绝对路径列表。
        """
        self.message = message
        self.json_path = json_path
        self.absolute_path = absolute_path
