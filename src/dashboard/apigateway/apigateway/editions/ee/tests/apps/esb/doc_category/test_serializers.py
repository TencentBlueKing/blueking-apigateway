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

from apigateway.apps.esb.bkcore.models import DocCategory
from apigateway.apps.esb.doc_category.serializers import DocCategorySLZ

pytestmark = [pytest.mark.django_db]


class TestDocCategorySLZ:
    @pytest.mark.parametrize(
        "data, context, expected",
        [
            (
                {
                    "name": "test",
                    "priority": 300,
                    "data_type": 1,
                },
                {},
                {
                    "name": "test",
                    "priority": 300,
                    "is_official": True,
                },
            ),
            (
                {
                    "name": "test-02",
                    "priority": 500,
                    "data_type": 3,
                },
                {
                    "system_counts": {},
                },
                {
                    "name": "test-02",
                    "priority": 500,
                    "is_official": False,
                    "system_count": 0,
                },
            ),
        ],
    )
    def test_to_representation(self, data, context, expected):
        doc_category = G(DocCategory, **data)
        slz = DocCategorySLZ(doc_category, context=context)

        expected.update(
            {
                "id": doc_category.id,
                "updated_time": slz.data["updated_time"],
            }
        )
        assert slz.data == expected

    @pytest.mark.parametrize(
        "data, expected, will_error",
        [
            (
                {
                    "name": "doc-category-test",
                    "priority": 300,
                },
                {
                    "name": "doc-category-test",
                    "priority": 300,
                },
                False,
            )
        ],
    )
    def test_validate(self, settings, data, expected, will_error):
        slz = DocCategorySLZ(data=data)
        slz.is_valid()

        expected["board"] = settings.ESB_DEFAULT_BOARD
        assert slz.validated_data == expected
