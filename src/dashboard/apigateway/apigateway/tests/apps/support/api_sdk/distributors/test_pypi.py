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

    source_tar = dist.join(f"{sdk_context.name}.tar.gz")
    source_tar.write("")
    return source_tar


@pytest.fixture
def sdk_context(sdk_context):
    sdk_context.language = ProgrammingLanguageEnum.PYTHON
    return sdk_context


def test_pypirc(
    tmpdir, faker, output_dir, python_setup_script, python_setup_history, sdist, distributor: PypiSourceDistributor
):
    distributor.distribute(output_dir, [sdist])

    pypirc_path = tmpdir.join(".pypirc")
    assert pypirc_path.exists()


def test_distribute(
    output_dir,
    sdk_context,
    python_setup_script,
    sdist,
    python_setup_history,
    distributor: PypiSourceDistributor,
    package_searcher_result,
):
    result = distributor.distribute(output_dir, [sdist])

    python_setup_history = python_setup_history.read()
    assert f"setup.py sdist upload -r {distributor.repository}" in python_setup_history

    assert sdk_context.config["python"]["is_uploaded_to_pypi"]
    assert sdk_context.config["python"]["repository"] == distributor.repository
    assert result.url == package_searcher_result.url
    assert not result.is_local
