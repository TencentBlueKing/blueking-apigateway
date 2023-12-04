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

from apigateway.biz.esb.system_doc_category import SystemDocCategoryHandler

pytestmark = pytest.mark.django_db


class TestSystemDocCategoryHandler:
    def test_get_system_doc_categories_by_db(self, mocker):
        mocker.patch(
            "apigateway.apps.esb.bkcore.models.SystemDocCategory.objects.group_category_id_by_board",
            # "apigateway.biz.esb.system_doc_category.SystemDocCategory.objects.group_category_id_by_board",
            return_value={
                "test": [1, 2],
            },
        )
        mocker.patch(
            "apigateway.apps.esb.bkcore.models.SystemDocCategory.objects.group_system_id_by_category_id",
            # "apigateway.biz.esb.system_doc_category.SystemDocCategory.objects.group_system_id_by_category_id",
            return_value={
                1: [1, 2],
                2: [3, 4],
            },
        )
        mocker.patch(
            "apigateway.apps.esb.bkcore.models.DocCategory.objects.get_id_to_fields_map",
            # "apigateway.biz.esb.system_doc_category.DocCategory.objects.get_id_to_fields_map",
            return_value={
                1: {"id": 1, "name": "c1", "priority": 1},
                2: {"id": 2, "name": "c2", "priority": 2},
            },
        )
        mocker.patch(
            "apigateway.biz.esb.system_doc_category.ComponentSystem.objects.get_id_to_fields_map",
            return_value={
                3: {"name": "s3", "description": "desc"},
                4: {"name": "s4", "description": "desc"},
            },
        )
        mocker.patch(
            "apigateway.biz.esb.system_doc_category.ESBChannel.objects.filter_active_and_public_system_ids",
            return_value=[3, 4],
        )
        mocker.patch(
            "apigateway.biz.esb.system_doc_category.BoardConfigManager.get_board_label",
            return_value="test-label",
        )

        result = SystemDocCategoryHandler._get_system_doc_categories_by_db()
        assert result == [
            {
                "board": "test",
                "board_label": "test-label",
                "categories": [
                    {
                        "id": 2,
                        "name": "c2",
                        "systems": [
                            {
                                "name": "s3",
                                "description": "desc",
                            },
                            {
                                "name": "s4",
                                "description": "desc",
                            },
                        ],
                    }
                ],
            }
        ]

    def test_get_system_doc_categories_by_settings(self):
        pass
