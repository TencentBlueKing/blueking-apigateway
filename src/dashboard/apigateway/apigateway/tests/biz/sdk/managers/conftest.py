#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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


def mock_factory(obj):
    def create(**kwargs):
        for k, v in kwargs.items():
            setattr(obj, k, v)

        return obj

    return create


@pytest.fixture
def mock_generator(mocker):
    return mocker.MagicMock()


@pytest.fixture
def mock_generator_cls(mocker, mock_generator):
    return mocker.MagicMock(side_effect=mock_factory(mock_generator))


@pytest.fixture
def mock_packager(mocker):
    return mocker.MagicMock()


@pytest.fixture
def mock_packager_cls(mocker, mock_packager):
    return mocker.MagicMock(side_effect=mock_factory(mock_packager))


@pytest.fixture
def mock_public_distributor(mocker):
    return mocker.MagicMock()


@pytest.fixture
def mock_public_distributor_cls(mocker, mock_public_distributor):
    return mocker.MagicMock(side_effect=mock_factory(mock_public_distributor))


@pytest.fixture
def mock_private_distributor(mocker):
    return mocker.MagicMock()


@pytest.fixture
def mock_private_distributor_cls(mocker, mock_private_distributor):
    return mocker.MagicMock(side_effect=mock_factory(mock_private_distributor))
