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
from enum import Enum
from typing import Any, List, Type

from django.core.management.base import BaseCommand
from pydantic import BaseModel, fields
from ruamel.yaml.comments import CommentedMap

from apigateway.controller.crds.v1beta1 import custom_resources as custom_resources_v1beta1
from apigateway.controller.crds.v1beta1.models.base import GatewayCustomResource
from apigateway.utils.yaml import yaml_dumps

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    custom_resources = {"v1beta1": custom_resources_v1beta1}

    def add_arguments(self, parser):
        parser.add_argument("--api-version-domain", type=str, default="gateway.bk.tencent.com", help="api 版本域")
        parser.add_argument("--api-version", type=str, default="v1beta1", help="api 版本")
        parser.add_argument("--kind", dest="kinds", nargs="*", help="指定类型")

    def get_field_comment(self, field: fields.ModelField):
        description = ""
        field_info = field.field_info
        if field_info.description:
            description = field_info.description

        type_description = ""
        if isinstance(field.type_, type):
            type_description = f"({field.type_.__name__})"

        flag_description = ""
        flags = []
        if field.required:
            flags.append("required")
        if field.allow_none:
            flags.append("optional")

        if flags:
            flag_description = f"[{','.join(flags)}]"

        return f"{description}{type_description}{flag_description}"

    def get_field_value_comment(self, field: fields.ModelField):
        if isinstance(field.type_, type) and issubclass(field.type_, Enum):
            return "/".join(e.value for e in field.type_)
        return None

    def get_complex_commented_dict_from_model_field(self, field: fields.ModelField, level: int):
        if field.shape == fields.SHAPE_SINGLETON:
            return self.get_commented_map_from_model(field.type_, level)

        if field.shape in {fields.SHAPE_LIST, fields.SHAPE_SET, fields.SHAPE_SEQUENCE, fields.SHAPE_TUPLE}:
            return [self.get_commented_map_from_model(field.type_, level)]

        if field.key_field:
            key = "<example>"
            result = CommentedMap({"<example>": self.get_commented_map_from_model(field.type_, level + 1)})
            result.yaml_set_comment_before_after_key(
                key=key, before=self.get_field_comment(field.key_field), indent=level * 2
            )
            return result
        return None

    def get_commented_map_from_model(self, model: Type[BaseModel], level: int):
        result = CommentedMap()

        for attr, field in model.__fields__.items():
            field_info = field.field_info
            if not field_info:
                continue

            if field.is_complex() and field.type_ is not Any and issubclass(field.type_, BaseModel):
                value = self.get_complex_commented_dict_from_model_field(field, level + 1)
            else:
                value = field.get_default()

            key = field.alias or attr
            result[key] = value
            comment = self.get_field_comment(field)
            if comment:
                result.yaml_set_comment_before_after_key(key=key, before=comment, indent=level * 2)

            comment = self.get_field_value_comment(field)
            if comment:
                result.yaml_add_eol_comment(key=key, comment=comment)

        return result

    def generate_example(
        self,
        api_version_domain: str,
        api_version: str,
        cr: Type[GatewayCustomResource],
    ):
        result = CommentedMap({"apiVersion": f"{api_version_domain}/{api_version}"})
        result.update(self.get_commented_map_from_model(cr, 0))
        return yaml_dumps(result)

    def handle(self, api_version_domain: str, api_version: str, kinds: List[str], **options):
        custom_resources = self.custom_resources[api_version]

        for cr in custom_resources:
            if kinds and cr.kind not in kinds:
                continue

            example = self.generate_example(api_version_domain, api_version, cr)
            print(f"----- {cr.kind} -----")
            print(example)
