# -*- coding: utf-8 -*-
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
import io

import pytest

from apigateway.utils.responses import DownloadableResponse

pytestmark = pytest.mark.no_meta_schema


class TestDownloadableResponse:
    @pytest.mark.parametrize(
        "charset, expected",
        [
            ("utf-8-sig", "\ufeffa,中文\r\n1,2\r\n".encode("utf-8")),
            ("utf-8", "a,中文\r\n1,2\r\n".encode("utf-8")),
        ],
    )
    def test_str_content_encoded_once(self, charset, expected):
        response = DownloadableResponse("a,中文\r\n1,2\r\n", filename="test.csv")
        response.charset = charset

        assert b"".join(response.streaming_content) == expected

    def test_bytes_content(self):
        response = DownloadableResponse(b"a,b\n", filename="test.yaml")

        assert b"".join(response.streaming_content) == b"a,b\n"

    def test_file_content(self):
        response = DownloadableResponse(io.BytesIO(b"zip-data"), filename="test.zip")

        assert b"".join(response.streaming_content) == b"zip-data"
        assert response["Content-Disposition"] == 'attachment;filename="test.zip"'
