# -*- coding: utf-8 -*-
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
from django.test import TestCase

from apigateway.apps.access_log.constants import ES_OUTPUT_FIELDS, ES_QUERY_FIELDS
from apigateway.apps.access_log.exceptions import NotScrubbedException
from apigateway.apps.access_log.helpers import (
    BKLogLogSearch,
    DataScrubber,
    DslESLogSearch,
    LogSearchFactory,
)
from apigateway.tests.utils.testing import dummy_time


class TestLogSearchFactory:
    @pytest.mark.parametrize(
        "es_client_type, expected",
        [
            (
                "bk_log",
                BKLogLogSearch,
            ),
            (
                "elasticsearch",
                DslESLogSearch,
            ),
        ],
    )
    def test_get_client_class(self, es_client_type, expected):
        result = LogSearchFactory().get_client_class(es_client_type)
        assert result == expected


class TestDslESLogSearch:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, mocker, settings):
        settings.ACCESS_LOG_CONFIG = {
            "es_client_type": "elasticsearch",
            "es_index": "test_index",
            "es_time_field_name": "@timestamp",
        }
        settings.ELASTICSEARCH_HOSTS = ["localhost"]

        mocker.patch.object(
            DslESLogSearch,
            "_es_index",
            new_callable=mocker.PropertyMock(return_value=settings.ACCESS_LOG_CONFIG["es_index"]),
        )
        mocker.patch.object(
            DslESLogSearch,
            "_es_time_field_name",
            new_callable=mocker.PropertyMock(return_value=settings.ACCESS_LOG_CONFIG["es_time_field_name"]),
        )
        mocker.patch.object(
            DslESLogSearch._es_client_class,
            "_hosts",
            new_callable=mocker.PropertyMock(return_value=settings.ELASTICSEARCH_HOSTS),
        )

    def test_es_index(self):
        client = DslESLogSearch()
        assert client._es_index == "test_index"

    def test_es_time_field_name(self):
        client = DslESLogSearch()
        assert client._es_time_field_name == "@timestamp"

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "api_id": 2,
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
                            "must": [{"query_string": {"fields": ES_QUERY_FIELDS, "query": "api_id: 2"}}],
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
        es_log_search = DslESLogSearch(
            api_id=params["api_id"],
            stage_name=params["stage_name"],
            time_start=params["time_start"],
            time_end=params["time_end"],
            query=params["query"],
        )
        s = es_log_search._build_logs_search(params["offset"], params["limit"], order=params["order"])
        assert s.to_dict() == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "api_id": 2,
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
                            "must": [{"query_string": {"fields": ES_QUERY_FIELDS, "query": "api_id: 2"}}],
                        }
                    },
                    "aggs": {
                        "histogram": {"date_histogram": {"field": "@timestamp", "interval": "10s", "min_doc_count": 1}}
                    },
                    "from": 0,
                    "size": 0,
                },
            )
        ],
    )
    def test_build_date_histogram_search(self, params, expected):
        es_log_search = DslESLogSearch(
            api_id=params["api_id"],
            stage_name=params["stage_name"],
            time_start=params["time_start"],
            time_end=params["time_end"],
            query=params["query"],
        )
        s = es_log_search._build_date_histogram_search()

        assert s.to_dict() == expected

    @pytest.mark.parametrize(
        "mocked_search_logs, expected",
        [
            (
                (1, [{"timestamp": dummy_time.timestamp}]),
                1,
            ),
        ],
    )
    def test_search_logs(self, mocker, mocked_search_logs, expected):
        mocker.patch(
            "apigateway.apps.access_log.helpers.DslESLogSearch.search_logs",
            return_value=mocked_search_logs,
        )

        es_log_client = DslESLogSearch(
            api_id=1,
            stage_name="prod",
            time_range=300,
        )
        total_count, logs = es_log_client.search_logs(
            offset=0,
            limit=2,
        )
        assert total_count == expected
        assert len(logs) == expected

    @pytest.mark.parametrize(
        "mocked_time_chart",
        [
            {
                "series": [7, 7],
                "timeline": [1579054140, 1579054200],
            },
        ],
    )
    def test_get_time_chart(self, mocker, mocked_time_chart):
        mocker.patch(
            "apigateway.apps.access_log.helpers.DslESLogSearch.get_time_chart",
            return_value=mocked_time_chart,
        )

        es_log_client = DslESLogSearch(
            api_id=1,
            stage_name="prod",
            time_range=3000,
        )
        result = es_log_client.get_time_chart()

        assert result["series"] == mocked_time_chart["series"]
        assert result["timeline"] == mocked_time_chart["timeline"]


class TestDataScrubber(TestCase):
    def test_contains_sensitive_data(self):
        data = [
            {
                "content": "",
                "expected": False,
            },
            {
                "content": '{"app_code": "test"}',
                "expected": False,
            },
            {
                "content": '{"app_secret": "xxx"}',
                "expected": True,
            },
            {
                "content": '{"bk_ticket": "xxx"}',
                "expected": True,
            },
        ]

        data_scrubber = DataScrubber()

        for test in data:
            result = data_scrubber._contains_sensitive_data(test["content"])
            self.assertEqual(result, test["expected"])

    def test_scrub_body(self):
        data = [
            # ok, json data, matched sensitive key
            {
                "content": '{"app_code": "test", "app_secret": "xxx"}',
                "expected": '{"app_code": "test", "app_secret": "***"}',
            },
            # ok, urlencoded data, matched sensitive key
            {
                "content": "app_code=test&app_secret=test",
                "expected": "app_code=test&app_secret=%2A%2A%2A",
            },
            # ok, json data, part matched sensitive key
            {
                "content": '{"app_code": "test", "my_password": "xxx"}',
                "expected": '{"app_code": "test", "my_password": "***"}',
            },
            # error, invalid json data
            {
                "content": '{"app_code": "test", "app_secr',
                "will_error": True,
            },
            # error, invalid urlencoded data
            {
                "content": "a=b&cd",
                "will_error": True,
            },
        ]

        data_scrubber = DataScrubber()

        for test in data:
            if test.get("will_error"):
                with self.assertRaises(NotScrubbedException):
                    result = data_scrubber._scrub_body(test["content"])
                continue

            result = data_scrubber._scrub_body(test["content"])
            self.assertEqual(result, test["expected"])

    def test_scrub_by_keys(self):
        data = [
            # ok, matched
            {
                "data": {
                    "app_code": "test",
                    "app_secret": "test",
                },
                "expected": {
                    "app_code": "test",
                    "app_secret": "***",
                },
            },
            # ok, part matched
            {
                "data": {
                    "app_code": "test",
                    "my_password": "test",
                },
                "expected": {
                    "app_code": "test",
                    "my_password": "***",
                },
            },
            # ok, no sensitive data
            {
                "data": {
                    "app_code": "test",
                    "at": "test",
                },
                "expected": {
                    "app_code": "test",
                    "at": "test",
                },
            },
            # ok, some value is empty
            {
                "data": {
                    "app_code": "test",
                    "at": "",
                },
                "expected": {
                    "app_code": "test",
                    "at": "",
                },
            },
        ]
        data_scrubber = DataScrubber()
        for test in data:
            result = data_scrubber._scrub_by_keys(test["data"])
            self.assertEqual(result, test["expected"])
