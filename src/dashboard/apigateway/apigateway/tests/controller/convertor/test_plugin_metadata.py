#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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

from apigateway.controller.convertor.plugin_metadata import PluginMetadataConvertor

pytestmark = pytest.mark.no_meta_schema


@pytest.mark.parametrize("apisix_version", ["3.13", "3.16", "3.18"])
def test_file_logger_metadata_includes_request_size_fields(apisix_version):
    metadata = PluginMetadataConvertor(apisix_version=apisix_version).convert()
    file_logger = next(item for item in metadata if item.id == "file-logger")
    log_format = file_logger.model_dump(exclude_none=True)["log_format"]

    assert log_format["request_size"] == "$request_length"
    assert log_format["content_length"] == "$content_length"
    assert log_format["response_size"] == "$body_bytes_sent"
