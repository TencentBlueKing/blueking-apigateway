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

from apigateway.common.error_codes import APIError, error_codes
from apigateway.service.es.clients import (
    BKLogESClient,
)


class TestBKLogESClientMixin:
    def test_execute_search(self, mocker, faker):
        es_index = faker.pystr()
        es_body = faker.pystr()

        es_client = BKLogESClient(es_index)

        mocker.patch(
            "apigateway.service.es.clients.esquery_dsl",
            side_effect=error_codes.REMOTE_REQUEST_ERROR,
        )
        with pytest.raises(APIError):
            es_client.execute_search(es_body)

        mocked_esquery_dsl = mocker.patch(
            "apigateway.service.es.clients.esquery_dsl",
            return_value={"test": 1},
        )
        result = es_client.execute_search(es_body)
        assert result == {"test": 1}
        mocked_esquery_dsl.assert_called_once_with(index=es_index, body=es_body)
