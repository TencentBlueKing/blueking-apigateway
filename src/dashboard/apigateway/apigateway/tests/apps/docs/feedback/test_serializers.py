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
from rest_framework import serializers as drf_serializers

from apigateway.apps.docs.feedback import serializers


class TestRelatedComponentSLZ:
    @pytest.mark.parametrize(
        "data, expected, will_error",
        [
            (
                {
                    "board": "open",
                    "system_name": "TEST",
                    "component_name": "test",
                },
                {
                    "board": "open",
                    "system_name": "TEST",
                    "component_name": "test",
                },
                False,
            ),
            (
                {
                    "board": "test",
                    "system_name": "TEST",
                    "component_name": "test",
                },
                None,
                True,
            ),
        ],
    )
    def test_validate(self, mock_board, data, expected, will_error):
        slz = serializers.RelatedComponentSLZ(data=data)
        slz.is_valid()

        if will_error:
            assert slz.errors
            return

        assert slz.validated_data == expected


class TestRelatedAPIGatewaySLZ:
    @pytest.mark.parametrize(
        "data, expected, will_error, mock_api, mock_resource",
        [
            (
                {
                    "api_name": "test1",
                    "stage_name": "prod",
                    "resource_name": "test",
                },
                {
                    "api_id": 1,
                    "stage_name": "prod",
                    "resource_id": 1,
                },
                False,
                {
                    "id": 1,
                },
                {
                    "id": 1,
                },
            ),
            (
                {
                    "api_name": "test",
                    "stage_name": "prod",
                    "resource_name": "test",
                },
                {},
                True,
                {},
                {
                    "id": 1,
                },
            ),
        ],
    )
    def test_validate(self, mocker, data, expected, will_error, mock_api, mock_resource):
        mocker.patch(
            "apigateway.apps.docs.feedback.serializers.support_helper.get_gateway_by_name",
            return_value=mock_api,
        )
        mocker.patch(
            "apigateway.apps.docs.feedback.serializers.support_helper.get_released_resource",
            return_value=mock_resource,
        )

        slz = serializers.RelatedAPIGatewaySLZ(data=data)
        slz.is_valid()

        if will_error:
            assert bool(slz.errors)
            return

        assert slz.validated_data == expected


class TestFeedbackCreateSLZ:
    @pytest.mark.parametrize(
        "doc_type, data, will_error",
        [
            (
                "component",
                {
                    "related_component": {"a": 1},
                },
                False,
            ),
            (
                "apigateway",
                {
                    "related_apigateway": {"a": 1},
                },
                False,
            ),
            (
                "platform",
                {},
                False,
            ),
            (
                "component",
                {},
                True,
            ),
            (
                "apigateway",
                {},
                True,
            ),
        ],
    )
    def test_validate_related_field(self, doc_type, data, will_error):
        slz = serializers.FeedbackCreateSLZ()

        if will_error:
            with pytest.raises(drf_serializers.ValidationError):
                slz.validate_related_field(doc_type, data)
            return

        result = slz.validate_related_field(doc_type, data)
        assert result is None
