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
from bkapi_client_core.exceptions import BKAPIError

from apigateway.common.error_codes import APIError
from apigateway.common.es.clients import (
    BKLogESClient,
)
from apigateway.components.exceptions import RemoteRequestError


class TestBKLogESClientMixin:
    def test_execute_search(self, mocker, faker):
        es_index = faker.pystr()
        es_body = faker.pystr()

        es_client = BKLogESClient(es_index)

        mocker.patch(
            "apigateway.common.es.clients.bk_log_component.esquery_dsl",
            side_effect=RemoteRequestError(faker.pystr, BKAPIError("error")),
        )
        with pytest.raises(APIError):
            es_client.execute_search(es_body)

        mocked_esquery_dsl = mocker.patch(
            "apigateway.common.es.clients.bk_log_component.esquery_dsl",
            return_value={"test": 1},
        )
        result = es_client.execute_search(es_body)
        assert result == {"test": 1}
        mocked_esquery_dsl.assert_called_once_with(index=es_index, body=es_body)
