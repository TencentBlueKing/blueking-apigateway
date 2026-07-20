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
import importlib

import pytest
from django.test import override_settings
from django.urls import NoReverseMatch, clear_url_caches, reverse, set_urlconf

import apigateway.urls
from apigateway.apis.v2.inner import serializers, views


class TestUrls:
    def test_inner_monitor_apis_own_pagination_parameters_once(self):
        assert "offset" not in serializers.AppAlarmRecordListInputSLZ().fields
        assert "limit" not in serializers.AppAlarmRecordListInputSLZ().fields
        assert views.AppRequestLogListApi.pagination_class is None

    def test_schema_generation_succeeds_with_explicit_query_parameters(self, caplog, client):
        try:
            with override_settings(DEBUG=True):
                clear_url_caches()
                importlib.reload(apigateway.urls)
                set_urlconf(None)

                response = client.get("/backend/docs/auto/swagger/?format=openapi")

                assert response.status_code == 200
                schema = response.json()
                alarm_record_parameters = schema["paths"]["/api/v2/inner/apps/{app_code}/monitor/alarm-records/"][
                    "get"
                ]["parameters"]
                alarm_record_parameter_names = [parameter["name"] for parameter in alarm_record_parameters]
                assert set(alarm_record_parameter_names) == {
                    "status",
                    "gateway_name",
                    "resource_name",
                    "time_start",
                    "time_end",
                    "offset",
                    "limit",
                }
                assert len(alarm_record_parameter_names) == len(set(alarm_record_parameter_names))

                workbench_parameters = schema["paths"]["/me/workbench/permissions/gateway/applied/"]["get"][
                    "parameters"
                ]
                workbench_parameter_names = [parameter["name"] for parameter in workbench_parameters]
                assert set(workbench_parameter_names) == {
                    "limit",
                    "offset",
                    "bk_app_code",
                    "applied_by",
                    "gateway_id",
                    "grant_dimension",
                    "time_start",
                    "time_end",
                    "keyword",
                    "status",
                }
                assert len(workbench_parameter_names) == len(set(workbench_parameter_names))
                assert "GatewayPublicKeyRetrieveApi.get_serializer raised exception" not in caplog.text
                assert "ResourceVersionGetLatestApi.get_serializer raised exception" not in caplog.text
        finally:
            importlib.reload(apigateway.urls)
            clear_url_caches()
            set_urlconf(None)

    def test_schema_json_url_uses_non_compat_format(self):
        try:
            with override_settings(DEBUG=True):
                clear_url_caches()
                importlib.reload(apigateway.urls)
                set_urlconf(None)

                assert reverse("schema-json", kwargs={"format": "json"}) == "/backend/docs/auto/swagger.json"
        finally:
            importlib.reload(apigateway.urls)
            clear_url_caches()
            set_urlconf(None)

    def test_urls_disabled_when_debug_is_false(self):
        try:
            with override_settings(DEBUG=False):
                clear_url_caches()
                importlib.reload(apigateway.urls)
                set_urlconf(None)

                with pytest.raises(NoReverseMatch):
                    reverse("schema-swagger-ui")
        finally:
            importlib.reload(apigateway.urls)
            clear_url_caches()
            set_urlconf(None)
