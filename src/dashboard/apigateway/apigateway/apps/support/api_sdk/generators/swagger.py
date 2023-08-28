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
import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List

from bkapi_client_generator import GenerateFailed, generate_client

from apigateway.apps.resource.swagger.swagger import ResourceSwaggerExporter
from apigateway.apps.support.api_sdk import exceptions
from apigateway.apps.support.api_sdk.models import Generator
from apigateway.core.constants import SwaggerFormatEnum
from apigateway.utils.file import write_to_file

logger = logging.getLogger(__name__)


@dataclass
class SwaggerTemplateGenerator(Generator):
    template_name: ClassVar[str] = "demo"

    def _generate_client(self, swagger_path, output_dir):
        try:
            return generate_client(
                name=self.context.name,
                client_package=self.context.package,
                swagger=swagger_path,
                template_name=self.template_name,
                output=output_dir,
            )
        except GenerateFailed as err:
            raise exceptions.GenerateError(
                f"failed to generate client package {self.context.name}, code: {err.code}"
            ) from err
        except Exception as err:
            raise exceptions.GenerateError(f"failed to generate client package {self.context.name}") from err

    def generate(self, output_dir: str, resources: List[Dict[str, Any]]):
        exporter = ResourceSwaggerExporter(
            api_version=self.context.version,
            title=self.context.resource_version.gateway.name,
            description=self.context.resource_version.gateway.description,
            include_bk_apigateway_resource=False,
        )

        swagger = exporter.to_swagger(resources, SwaggerFormatEnum.YAML.value)

        with tempfile.TemporaryDirectory() as temp_dir:
            swagger_path = os.path.join(temp_dir, "swagger.yaml")
            write_to_file(swagger, swagger_path)

            package_dir = self._generate_client(
                swagger_path=swagger_path,
                output_dir=temp_dir,
            )

            for name in os.listdir(package_dir):
                shutil.move(os.path.join(package_dir, name), output_dir)


class PythonTemplateGenerator(SwaggerTemplateGenerator):
    template_name = "bkapi_python"


class GolangTemplateGenerator(SwaggerTemplateGenerator):
    template_name = "bkapi_golang"
