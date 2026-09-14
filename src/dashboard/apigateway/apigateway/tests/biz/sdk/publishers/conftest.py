#
# TencentBlueKing is pleased to support the open source community by making
# BlueKing - APIGateway available.
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
import pytest

from apigateway.biz.sdk.artifacts import create_built_artifact
from apigateway.biz.sdk.config import SDKLanguageConfig


@pytest.fixture
def built_artifact(tmp_path):
    def factory(artifact_type, filename, content=b"content"):
        path = tmp_path / filename
        path.write_bytes(content)
        return create_built_artifact(artifact_type, path, allowed_roots=(tmp_path,))

    return factory


@pytest.fixture
def python_config():
    return SDKLanguageConfig(
        language="python",
        generator_name="python",
        project_name="bkapi-demo",
        package_name="bkapi_demo",
        package_version="1.2.3",
        additional_properties={
            "packageName": "bkapi_demo",
            "packageVersion": "1.2.3",
            "projectName": "bkapi-demo",
            "buildSystem": "poetry",
        },
        native_distributor="pypi",
    )


@pytest.fixture
def java_config():
    return SDKLanguageConfig(
        language="java",
        generator_name="java",
        project_name="bkapi-demo",
        package_name="com.tencent.bk.bkapi.demo",
        package_version="1.2.3",
        additional_properties={
            "groupId": "com.tencent.bk.bkapi",
            "artifactId": "bkapi-demo",
            "artifactVersion": "1.2.3",
            "invokerPackage": "com.tencent.bk.bkapi.demo",
            "apiPackage": "com.tencent.bk.bkapi.demo.api",
            "modelPackage": "com.tencent.bk.bkapi.demo.model",
            "library": "native",
        },
        native_distributor="maven",
    )
