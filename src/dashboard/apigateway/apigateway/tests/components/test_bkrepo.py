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
from pathlib import Path

from blue_krill.storages.blobstore.exceptions import RequestError

from apigateway.components.bkrepo import BKRepoComponent


def test_generic_file_wrappers_delegate(mocker, tmp_path):
    component = BKRepoComponent("https://repo", "user", "password", "project", "bucket")
    client = mocker.patch.object(component, "_generic_client")
    client.download_file.return_value = tmp_path / "download"

    assert component.download_generic_file("key", str(tmp_path / "download")) == tmp_path / "download"
    component.delete_generic_file("key")
    client.get_file_metadata.return_value = {"Content-Length": "1"}
    assert component.get_generic_file_metadata("key") == {"Content-Length": "1"}

    client.download_file.assert_called_once_with(key="key", filepath=Path(tmp_path / "download"))
    client.delete_file.assert_called_once_with(key="key")


def test_get_generic_file_metadata_maps_only_404_to_none(mocker):
    component = BKRepoComponent("https://repo", "user", "password", "project", "bucket")
    client = mocker.patch.object(component, "_generic_client")
    client.get_file_metadata.side_effect = RequestError("missing", code="404")

    assert component.get_generic_file_metadata("missing") is None


def test_delete_generic_file_maps_404_to_idempotent_success(mocker):
    component = BKRepoComponent("https://repo", "user", "password", "project", "bucket")
    client = mocker.patch.object(component, "_generic_client")
    client.delete_file.side_effect = RequestError("missing", code="404")

    assert component.delete_generic_file("missing") is None
