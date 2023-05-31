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
from ddf import G

from apigateway.apps.docs.feedback import factories, models
from apigateway.apps.docs.feedback.constants import DocTypeEnum
from apigateway.common.error_codes import APIError

pytestmark = pytest.mark.django_db


class TestFeedbackRelatedObjectFactory:
    @pytest.mark.parametrize(
        "doc_type, model, will_error",
        [
            (
                DocTypeEnum.COMPONENT.value,
                factories.ReleatedComponent,
                False,
            ),
            (
                DocTypeEnum.APIGATEWAY.value,
                factories.RelatedAPIGateway,
                False,
            ),
            (
                DocTypeEnum.PLATFORM.value,
                None,
                True,
            ),
            (
                "",
                None,
                True,
            ),
        ],
    )
    def test_get(self, doc_type, model, will_error):
        if will_error:
            with pytest.raises(APIError):
                factories.FeedbackRelatedObjectFactory.get(doc_type)
            return

        result = factories.FeedbackRelatedObjectFactory.get(doc_type)
        assert isinstance(result, model)


class TestReleatedComponent:
    @pytest.mark.parametrize(
        "data",
        [
            {
                "board": "open",
                "system_name": "TEST",
                "component_name": "test",
            },
            {
                "board": "open",
                "system_name": "TEST",
            },
        ],
    )
    def test_create(self, data):
        obj = factories.ReleatedComponent()

        feedback = G(models.Feedback)

        result = obj.create(feedback, data)
        assert result.feedback.id == feedback.id
        assert isinstance(result, models.FeedbackRelatedComponent)


class TestReleatedRelatedAPIGateway:
    @pytest.mark.parametrize(
        "data",
        [
            {
                "api_id": 1,
                "stage_name": "prod",
                "resource_id": 1,
            },
            {
                "api_id": 1,
            },
        ],
    )
    def test_create(self, data):
        obj = factories.RelatedAPIGateway()

        feedback = G(models.Feedback)

        result = obj.create(feedback, data)
        assert result.feedback.id == feedback.id
        assert isinstance(result, models.FeedbackRelatedAPIGateway)
