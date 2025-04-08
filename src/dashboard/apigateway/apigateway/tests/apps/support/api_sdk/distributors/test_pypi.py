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
import os
import subprocess
from unittest.mock import patch

import pytest

from apigateway.apps.support.api_sdk.distributors.pypi import PypiSourceDistributor
from apigateway.apps.support.constants import ProgrammingLanguageEnum


@pytest.fixture
def package_searcher(mocker):
    return mocker.MagicMock()


@pytest.fixture
def package_searcher_result(mocker, package_searcher, faker):
    result = mocker.MagicMock(url=faker.url())
    package_searcher.search.return_value = result
    return result


@pytest.fixture
def distributor(faker, mocker, sdk_context, settings, package_searcher):
    settings.PYPI_MIRRORS_CONFIG = {
        PypiSourceDistributor.repository: {
            "index_url": "",
            "repository_url": faker.url(),
            "username": faker.user_name(),
            "password": faker.password(),
        }
    }

    distributor = PypiSourceDistributor(
        context=sdk_context,
    )
    distributor.package_searcher = package_searcher

    return distributor


@pytest.fixture
def sdist(tmpdir, sdk_context):
    dist = tmpdir.join("dist")
    dist.mkdir()

    # Create a simple package structure
    package_dir = tmpdir.join(sdk_context.name)
    package_dir.mkdir()

    init_file = package_dir.join("__init__.py")
    init_file.write("# Sample package")

    # Create a setup.py file with necessary metadata
    setup_py = tmpdir.join("setup.py")
    setup_py.write(f"""\
from setuptools import setup, find_packages

setup(
    name='{sdk_context.name}',
    version='1.0.0',
    packages=find_packages(),
    description='A test Python package',
    author='Your Name',
    author_email='test@example.com',
    url='https://example.com',
)
""")

    # Build the source distribution
    current_dir = os.getcwd()
    os.chdir(tmpdir)
    try:
        subprocess.check_call([os.sys.executable, "setup.py", "sdist"])
    finally:
        os.chdir(current_dir)
    return dist.join(f"{sdk_context.name}-1.0.0.tar.gz")


@pytest.fixture
def sdk_context(sdk_context):
    sdk_context.language = ProgrammingLanguageEnum.PYTHON
    return sdk_context


def test_pypirc(
    tmpdir, faker, output_dir, python_setup_script, python_setup_history, sdist, distributor: PypiSourceDistributor
):
    with patch("apigateway.apps.support.api_sdk.distributors.pypi.check_call") as mock_check_call:
        mock_check_call.return_value = 0  # Simulate successful execution
        distributor.distribute(output_dir, [sdist])

    pypirc_path = tmpdir.join(".pypirc")
    assert pypirc_path.exists()


def test_distribute(
    output_dir,
    sdk_context,
    sdist,
    distributor: PypiSourceDistributor,
    package_searcher_result,
):
    # Mock the check_call to prevent actual call to `twine upload`
    with patch("apigateway.apps.support.api_sdk.distributors.pypi.check_call") as mock_check_call:
        mock_check_call.return_value = 0  # Simulate successful execution
        result = distributor.distribute(output_dir, [sdist])

    assert sdk_context.config["python"]["is_uploaded_to_pypi"]
    assert sdk_context.config["python"]["repository"] == distributor.repository
    assert result.url == package_searcher_result.url
    assert not result.is_local
