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

from apigateway.biz.access_log.constants import ES_OUTPUT_FIELDS
from apigateway.biz.access_log.log_search import LogSearchClient


class TestLogSearchClient:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, mocker, settings):
        settings.ACCESS_LOG_CONFIG = {
            "es_client_type": "elasticsearch",
            "es_index": "test_index",
            "es_time_field_name": "@timestamp",
        }
        settings.ELASTICSEARCH_HOSTS = ["localhost"]

        mocker.patch.object(
            LogSearchClient,
            "_es_index",
            new_callable=mocker.PropertyMock(return_value=settings.ACCESS_LOG_CONFIG["es_index"]),
        )
        mocker.patch.object(
            LogSearchClient,
            "_es_time_field_name",
            new_callable=mocker.PropertyMock(return_value=settings.ACCESS_LOG_CONFIG["es_time_field_name"]),
        )

    def test_es_index(self):
        client = LogSearchClient()
        assert client._es_index == "test_index"

    def test_es_time_field_name(self):
        client = LogSearchClient()
        assert client._es_time_field_name == "@timestamp"

    @pytest.mark.parametrize(
        "mocked_search_logs, expected",
        [
            (
                {
                    "hits": {
                        "total": 1,
                        "hits": [
                            {
                                "_source": {"foo": "bar"},
                                "sort": [1690269157000],
                            }
                        ],
                    }
                },
                (1, [{"foo": "bar", "timestamp": 1690269157}]),
            ),
        ],
    )
    def test_search_logs(self, mocker, mocked_search_logs, expected):
        client = LogSearchClient(
            gateway_id=1,
            stage_name="prod",
            time_range=300,
        )
        mocker.patch.object(
            client,
            "_es_client",
            new_callable=mocker.PropertyMock(
                return_value=mocker.Mock(execute_search=mocker.Mock(return_value=mocked_search_logs))
            ),
        )
        total_count, logs = client.search_logs(
            offset=0,
            limit=2,
        )
        assert total_count == expected[0]
        assert logs == expected[1]

    @pytest.mark.parametrize(
        "mocked_time_chart, expected",
        [
            (
                {
                    "aggregations": {
                        "histogram": {
                            "buckets": [
                                {
                                    "key": 1579054140000,
                                    "doc_count": 7,
                                },
                                {
                                    "key": 1579054200000,
                                    "doc_count": 8,
                                },
                            ]
                        }
                    }
                },
                {
                    "series": [7, 8],
                    "timeline": [1579054140, 1579054200],
                },
            )
        ],
    )
    def test_get_time_chart(self, mocker, mocked_time_chart, expected):
        client = LogSearchClient(
            gateway_id=1,
            stage_name="prod",
            time_range=3000,
        )
        mocker.patch.object(
            client,
            "_es_client",
            new_callable=mocker.PropertyMock(
                return_value=mocker.Mock(execute_search=mocker.Mock(return_value=mocked_time_chart))
            ),
        )

        result = client.get_time_chart()
        assert result == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "time_start": 1578904866,
                    "time_end": 1578905166,
                    "query": "api_id: 2",
                    "offset": 0,
                    "limit": 2,
                    "order": True,
                },
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {"term": {"api_id": 2}},
                                {"term": {"stage": "prod"}},
                                {"range": {"@timestamp": {"gte": 1578904866000, "lte": 1578905166000}}},
                            ],
                            "must": [{"query_string": {"query": "api_id: 2"}}],
                        }
                    },
                    "sort": [{"@timestamp": {"order": "desc"}}],
                    "_source": ES_OUTPUT_FIELDS,
                    "from": 0,
                    "size": 2,
                },
            )
        ],
    )
    def test_build_logs_search(self, params, expected):
        client = LogSearchClient(
            gateway_id=params["gateway_id"],
            stage_name=params["stage_name"],
            time_start=params["time_start"],
            time_end=params["time_end"],
            query=params["query"],
        )
        s = client._build_logs_search(params["offset"], params["limit"], order=params["order"])
        assert s.to_dict() == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "time_start": 1578904866,
                    "time_end": 1578905166,
                    "query": "api_id: 2",
                },
                {
                    "query": {
                        "bool": {
                            "filter": [
                                {"term": {"api_id": 2}},
                                {"term": {"stage": "prod"}},
                                {"range": {"@timestamp": {"gte": 1578904866000, "lte": 1578905166000}}},
                            ],
                            "must": [{"query_string": {"query": "api_id: 2"}}],
                        }
                    },
                    "aggs": {
                        "histogram": {
                            "date_histogram": {
                                "field": "@timestamp",
                                "fixed_interval": "10s",
                                "min_doc_count": 0,
                                "extended_bounds": {
                                    "min": 1578904866000,
                                    "max": 1578905166000,
                                },
                            }
                        }
                    },
                    "from": 0,
                    "size": 0,
                },
            )
        ],
    )
    def test_build_date_histogram_search(self, params, expected):
        client = LogSearchClient(
            gateway_id=params["gateway_id"],
            stage_name=params["stage_name"],
            time_start=params["time_start"],
            time_end=params["time_end"],
            query=params["query"],
        )
        s = client._build_date_histogram_search()

        assert s.to_dict() == expected

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {"histogram": {}},
                {"series": [], "timeline": []},
            ),
            (
                {
                    "histogram": {
                        "buckets": [
                            {
                                "key": 1690269157000,
                                "doc_count": 5,
                            }
                        ]
                    }
                },
                {
                    "series": [5],
                    "timeline": [1690269157],
                },
            ),
        ],
    )
    def test_convert_histogram_buckets(self, data, expected):
        client = LogSearchClient()
        result = client._convert_histogram_buckets(data)
        assert result == expected

    @pytest.mark.parametrize(
        "hit, expected",
        [
            (
                {
                    "sort": [1690269157000],
                    "_source": {"foo": "bar"},
                },
                {
                    "foo": "bar",
                    "timestamp": 1690269157,
                },
            )
        ],
    )
    def test_to_log_display(self, hit, expected):
        client = LogSearchClient()
        result = client._to_log_display(hit)
        assert result == expected
