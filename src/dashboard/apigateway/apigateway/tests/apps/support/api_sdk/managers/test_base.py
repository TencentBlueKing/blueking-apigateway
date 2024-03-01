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

from apigateway.apps.support.api_sdk.exceptions import DistributeError
from apigateway.apps.support.api_sdk.managers.base import BaseSDKManager


@pytest.fixture
def manager(
    mock_generator_cls,
    mock_packager_cls,
    mock_public_distributor_cls,
    mock_private_distributor_cls,
    sdk_context,
    mocker,
):
    manager = BaseSDKManager()
    mocker.patch.object(manager, "generator_cls", mock_generator_cls)
    mocker.patch.object(manager, "packager_cls", mock_packager_cls)
    mocker.patch.object(manager, "public_distributor_cls", mock_public_distributor_cls)
    mocker.patch.object(manager, "private_distributor_cls", mock_private_distributor_cls)
    mocker.patch.object(manager, "get_context", return_value=sdk_context)

    return manager


class TestBaseSDKManager:
    @pytest.mark.parametrize(
        "include_private_resources, resource, expected",
        [
            (
                False,
                {
                    "method": "GET",
                    "is_public": True,
                },
                True,
            ),
            (
                True,
                {
                    "method": "GET",
                    "is_public": False,
                },
                True,
            ),
            (
                True,
                {
                    "method": "ANY",
                    "is_public": True,
                },
                False,
            ),
            (
                False,
                {
                    "method": "GET",
                    "is_public": False,
                },
                False,
            ),
        ],
    )
    def test_should_included_to_sdk(self, manager, include_private_resources, resource, expected):
        manager.include_private_resources = include_private_resources
        result = manager._should_included_to_sdk(resource)
        assert result is expected


def test_get_private_resources(
    resource_version,
    sdk_context,
    private_api_resources,
    public_api_resources,
    manager,
):
    manager.include_private_resources = True
    resources = manager.get_resources(sdk_context)

    for resource in private_api_resources:
        assert resource in resources

    for resource in public_api_resources:
        assert resource in resources


def test_get_public_resources(
    resource_version,
    sdk_context,
    private_api_resources,
    public_api_resources,
    manager,
):
    manager.include_private_resources = False
    resources = manager.get_resources(sdk_context)

    for resource in private_api_resources:
        assert resource not in resources

    for resource in public_api_resources:
        assert resource in resources


def test_get_generator(sdk_context, manager):
    generator = manager.get_generator(sdk_context)

    assert generator.context is sdk_context


def test_get_packager(sdk_context, manager):
    packager = manager.get_packager(sdk_context)

    assert packager.context is sdk_context


def test_get_distributor(sdk_context, manager):
    distributor = manager.get_distributor(sdk_context)

    assert distributor.context is sdk_context


def test_get_context(resource_version):
    manager = BaseSDKManager()

    with pytest.raises(NotImplementedError):
        manager.get_context(resource_version)


def test_handle_with_distributed(
    sdk_context,
    manager,
    resource_version,
    output_dir,
    public_api_resources,
    private_api_resources,
    mock_generator,
    mock_packager,
    mock_public_distributor,
    mock_private_distributor,
    faker,
):
    sdk_context.is_public = True
    files = [faker.file_path()]
    mock_packager.pack.return_value = files

    assert manager.handle(output_dir, resource_version) is sdk_context

    assert sdk_context.is_distributed

    mock_generator.generate.assert_called_once_with(output_dir, public_api_resources)
    mock_packager.pack.assert_called_once_with(output_dir)
    mock_public_distributor.distribute.assert_called_once_with(output_dir, files)
    mock_private_distributor.distribute.assert_not_called()


def test_handle_with_non_public_context(
    sdk_context,
    manager,
    resource_version,
    output_dir,
    public_api_resources,
    private_api_resources,
    mock_generator,
    mock_packager,
    mock_public_distributor,
    mock_private_distributor,
    faker,
):
    sdk_context.is_public = False
    files = [faker.file_path()]
    mock_packager.pack.return_value = files

    assert manager.handle(output_dir, resource_version) is sdk_context

    assert not sdk_context.is_distributed

    mock_generator.generate.assert_called_once_with(output_dir, public_api_resources)
    mock_packager.pack.assert_called_once_with(output_dir)
    mock_public_distributor.distribute.assert_not_called()
    mock_private_distributor.distribute.assert_called_once_with(output_dir, files)


def test_handle_with_private_distributor_failed(
    sdk_context,
    manager,
    resource_version,
    output_dir,
    public_api_resources,
    mock_generator,
    mock_packager,
    mock_private_distributor,
    faker,
):
    sdk_context.is_public = False
    files = [faker.file_path()]
    mock_packager.pack.return_value = files
    mock_private_distributor.distribute.side_effect = DistributeError

    assert manager.handle(output_dir, resource_version) is sdk_context


def test_handle_with_public_distributor_failed(
    sdk_context,
    manager,
    resource_version,
    output_dir,
    public_api_resources,
    mock_generator,
    mock_packager,
    mock_public_distributor,
    faker,
):
    sdk_context.is_public = True
    files = [faker.file_path()]
    mock_packager.pack.return_value = files
    mock_public_distributor.distribute.side_effect = DistributeError

    with pytest.raises(DistributeError):
        manager.handle(output_dir, resource_version)
