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
from elasticsearch.exceptions import AuthenticationException, ConnectionError, ConnectionTimeout, NotFoundError
from urllib3.exceptions import ConnectTimeoutError

from apigateway.common.error_codes import APIError
from apigateway.common.es.clients import (
    BaseESClient,
    BKLogESClient,
    DslESClient,
    ElasticsearchGetter,
    ESClientFactory,
    RawESClient,
)
from apigateway.components.exceptions import RemoteRequestError


class TestElasticsearchGetter:
    def test_get_elasticsearch(self, mocker):
        getter = ElasticsearchGetter()

        mocker.patch.object(getter, "_hosts", new_callable=mocker.PropertyMock(return_value=None))
        with pytest.raises(APIError):
            getter._get_elasticsearch()

        mocker.patch.object(getter, "_hosts", new_callable=mocker.PropertyMock(return_value="es-hosts"))
        mocker.patch("apigateway.common.es.clients.Elasticsearch", return_value=mocker.MagicMock())
        assert getter._get_elasticsearch() is not None

        mocker.patch.object(getter, "_hosts", new_callable=mocker.PropertyMock(return_value="es-hosts"))
        mocker.patch("apigateway.common.es.clients.Elasticsearch", side_effect=Exception)
        with pytest.raises(APIError):
            getter._get_elasticsearch()

    def test_get_es_hosts_display(self, settings):
        getter = ElasticsearchGetter()

        settings.ELASTICSEARCH_HOSTS_WITHOUT_AUTH = None
        assert getter._get_es_hosts_display() == ""

        settings.ELASTICSEARCH_HOSTS_WITHOUT_AUTH = ["1.0.0.1:9200"]
        assert getter._get_es_hosts_display() == "1.0.0.1:9200"

    def test_get_es_search_timeout(self):
        getter = ElasticsearchGetter()
        assert getter._get_es_search_timeout() == 30


class TestBaseESClient:
    def test_get_es_index(self):
        es_client = BaseESClient("index")
        assert es_client._get_es_index() == "index"


class TestDslESClient:
    def test_execute_search_with_dsl_search(self, mocker, faker):
        es_client = DslESClient(faker.pystr())

        response = mocker.MagicMock(success=mocker.MagicMock(return_value=True))
        s = mocker.MagicMock(execute=mocker.MagicMock(return_value=response))
        assert es_client.execute_search_with_dsl_search(s) == response

    def test_execute_search_with_dsl_search_response_fail(self, mocker, faker):
        es_client = DslESClient(faker.pystr())

        response = mocker.MagicMock(success=mocker.MagicMock(return_value=False))
        s = mocker.MagicMock(
            execute=mocker.MagicMock(return_value=response), to_dict=mocker.MagicMock(return_value={})
        )
        with pytest.raises(APIError):
            es_client.execute_search_with_dsl_search(s)

    @pytest.mark.parametrize(
        "exception",
        [
            ConnectionError(500, "error", {}),
            ConnectionTimeout(500, "error", {}),
            ConnectTimeoutError,
            NotFoundError,
            AuthenticationException,
            Exception,
        ],
    )
    def test_execute_search_with_dsl_search_error(self, mocker, faker, exception):
        es_client = DslESClient(faker.pystr())

        s = mocker.MagicMock(
            execute=mocker.MagicMock(side_effect=exception), to_dict=mocker.MagicMock(return_value={})
        )

        with pytest.raises(APIError):
            es_client.execute_search_with_dsl_search(s)


class TestRawESClient:
    def test_execute_search(self, mocker, faker):
        es_index = faker.pystr()
        es_body = faker.pystr()
        es_client = RawESClient(es_index)

        mocked_search = mocker.MagicMock(return_value={"result": True})
        mocker.patch.object(es_client, "_get_elasticsearch", return_value=mocker.MagicMock(search=mocked_search))

        result = es_client.execute_search(es_body)
        assert result == {"result": True}
        mocked_search.assert_called_once_with(index=es_index, body=es_body)

    @pytest.mark.parametrize(
        "exception",
        [
            ConnectionError(500, "error", {}),
            ConnectionTimeout(500, "error", {}),
            ConnectTimeoutError,
            NotFoundError,
            AuthenticationException,
            Exception,
        ],
    )
    def test_execute_search_error(self, mocker, faker, exception):
        mocked_search = mocker.MagicMock(side_effect=exception)
        es_client = mocker.MagicMock(search=mocked_search)

        es_client = RawESClient(faker.pystr())
        with pytest.raises(APIError):
            es_client.execute_search(faker.pystr())


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


class TestESClientFactory:
    def test_get_es_client(self, settings):
        settings.ACCESS_LOG_CONFIG["es_client_type"] = "bk_log"
        client = ESClientFactory.get_es_client("index")
        assert isinstance(client, BKLogESClient)

        settings.ACCESS_LOG_CONFIG["es_client_type"] = "elasticsearch"
        client = ESClientFactory.get_es_client("index")
        assert isinstance(client, RawESClient)

        settings.ACCESS_LOG_CONFIG["es_client_type"] = "not-exist"
        with pytest.raises(ValueError):
            ESClientFactory.get_es_client("index")
