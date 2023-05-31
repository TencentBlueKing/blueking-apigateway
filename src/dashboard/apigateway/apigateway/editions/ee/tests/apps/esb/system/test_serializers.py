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

from apigateway.apps.esb.bkcore.models import ComponentSystem, DocCategory
from apigateway.apps.esb.system.serializers import SystemSLZ

pytestmark = [pytest.mark.django_db]


class TestSystemSLZ:
    @pytest.fixture
    def mock_system_data(self):
        return {
            "name": "test",
            "description": "desc",
            "comment": "comment",
            "timeout": 30,
            "_maintainers": "",
        }

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "name": "test",
                    "description": "desc",
                    "description_en": None,
                    "comment": "comment",
                    "timeout": 30,
                    "data_type": 3,
                    "_maintainers": "",
                },
                {
                    "name": "test",
                    "description": "desc",
                    "description_en": None,
                    "comment": "comment",
                    "timeout": 30,
                    "maintainers": [],
                    "is_official": False,
                },
            ),
            (
                {
                    "name": "test-02",
                    "description": "desc",
                    "description_en": "desc_en",
                    "comment": "comment",
                    "timeout": 30,
                    "data_type": 3,
                    "_maintainers": "",
                },
                {
                    "name": "test-02",
                    "description": "desc",
                    "description_en": "desc_en",
                    "comment": "comment",
                    "timeout": 30,
                    "maintainers": [],
                    "is_official": False,
                },
            ),
        ],
    )
    def test_to_representation(self, data, expected):
        system = G(ComponentSystem, **data)
        expected.update(
            {
                "id": system.id,
            }
        )
        slz = SystemSLZ(
            system,
            context={
                "system_id_to_doc_category_map": {
                    system.id: {
                        "id": 2,
                        "name": "test",
                        "name_en": "test_en",
                    },
                },
                "system_id_to_channel_count_map": {system.id: 3},
            },
        )
        expected["doc_category_id"] = 2
        expected["doc_category_name"] = "test"
        expected["component_count"] = 3
        assert slz.data == expected

    @pytest.mark.parametrize(
        "data, expected, will_error",
        [
            (
                {
                    "name": "test_validate",
                    "description": "desc",
                    "description_en": "desc_en",
                    "comment": "comment",
                    "timeout": None,
                    "maintainers": [],
                },
                {
                    "name": "test_validate",
                    "description": "desc",
                    "description_en": "desc_en",
                    "comment": "comment",
                    "timeout": None,
                    "maintainers": [],
                },
                False,
            )
        ],
    )
    def test_validate(self, settings, data, expected, will_error):
        doc_category = G(DocCategory, board=settings.ESB_DEFAULT_BOARD)
        data["doc_category_id"] = doc_category.id

        slz = SystemSLZ(data=data)
        slz.is_valid()

        expected.update(
            {
                "board": settings.ESB_DEFAULT_BOARD,
                "doc_category_id": doc_category.id,
                "doc_category": doc_category,
            }
        )
        assert slz.validated_data == expected
