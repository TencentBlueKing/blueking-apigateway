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
import json
from pathlib import Path
from typing import cast

import pytest
from django_dynamic_fixture import G

from apigateway.apps.support.api_sdk.models import SDKContext
from apigateway.apps.support.constants import ProgrammingLanguageEnum
from apigateway.core.models import ResourceVersion


@pytest.fixture
def public_api_resources(faker):
    return [
        {
            "id": faker.pyint(),
            "name": faker.pystr(),
            "description": faker.pystr(),
            "method": "GET" if faker.pybool() else "POST",
            "path": f"/{faker.pystr()}/",
            "match_subpath": False,
            "is_public": True,
            "disabled_stages": [],
            "api_labels": [],
        }
        for _ in range(3)
    ]


@pytest.fixture
def private_api_resources(faker):
    return [
        {
            "id": faker.pyint(),
            "name": faker.pystr(),
            "description": faker.pystr(),
            "method": "GET" if faker.pybool() else "POST",
            "path": f"/{faker.pystr()}/",
            "match_subpath": False,
            "is_public": False,
            "disabled_stages": [],
            "api_labels": [],
        }
        for _ in range(3)
    ]


@pytest.fixture
def resource_version_data(public_api_resources, private_api_resources):
    resources = []
    resources.extend(private_api_resources)
    resources.extend(public_api_resources)
    return resources


@pytest.fixture
def resource_version(fake_gateway, resource_version_data, faker):
    resource_version = cast(
        ResourceVersion,
        G(
            ResourceVersion,
            gateway=fake_gateway,
            name=faker.pystr(),
            title=faker.pystr(),
            comment=faker.pystr(),
            _data=json.dumps(resource_version_data),
            created_time=faker.date_time(),
        ),
    )
    yield resource_version
    resource_version.delete()


@pytest.fixture
def sdk_context_version(faker):
    return f"1.{faker.pyint()}.{faker.pyint()}"


@pytest.fixture
def sdk_context(resource_version, sdk_context_version, faker):
    return SDKContext(
        name="test",
        package="test",
        resource_version=resource_version,
        version=sdk_context_version,
        language=ProgrammingLanguageEnum.UNKNOWN,
        is_public=True,
        is_latest=True,
    )


@pytest.fixture
def output_dir(tmpdir):
    return str(tmpdir)


@pytest.fixture
def python_setup_history(tmpdir):
    return tmpdir.join("setup.history")


@pytest.fixture
def python_setup_script(tmpdir):
    setup_py = tmpdir.join("setup.py")
    setup_py.write(
        r"""
import os
import sys

with open(os.path.join(os.path.dirname(__file__), "setup.history"), "at") as fp:
    cmds = " ".join(sys.argv)
    fp.write(cmds + "\n")
    """
    )

    return setup_py


@pytest.fixture
def output_dir_files(output_dir):
    root = Path(output_dir)
    files = set()

    for parts in [
        ["README.md"],
        ["src", "client.code"],
        ["src", "operation.code"],
    ]:
        target = root.joinpath(*parts)
        target.parent.mkdir(exist_ok=True)
        target.write_text("")
        files.add(target.relative_to(root).as_posix())

    return files
