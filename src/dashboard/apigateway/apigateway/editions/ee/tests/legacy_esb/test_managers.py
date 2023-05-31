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

from apigateway.legacy_esb import models as legacy_models

pytestmark = pytest.mark.django_db


class TestSystemDocCategory:
    @pytest.mark.parametrize(
        "mock_values, expected",
        [
            (["test", "test1", "test2"], []),
            (["test", "test1", "test"], ["test"]),
        ],
    )
    def test_get_duplicate_names(self, mocker, mock_values, expected):
        mocker.patch(
            "apigateway.legacy_esb.managers.SystemDocCategoryManager.values_list",
            return_value=mock_values,
        )
        result = legacy_models.SystemDocCategory.objects.get_duplicate_names()
        assert result == expected

    def test_delete_duplicate_names(self, mocker, unique_id):
        category1 = G(legacy_models.SystemDocCategory, name=unique_id)
        category2 = G(legacy_models.SystemDocCategory, name=unique_id)
        system1 = G(legacy_models.ComponentSystem, doc_category_id=category1.id)
        system2 = G(legacy_models.ComponentSystem, doc_category_id=category2.id)
        system3 = G(legacy_models.ComponentSystem, doc_category_id=category2.id)

        mocker.patch(
            "apigateway.legacy_esb.managers.SystemDocCategoryManager.get_duplicate_names",
            return_value=[unique_id],
        )

        legacy_models.SystemDocCategory.objects.delete_duplicate_names()

        assert legacy_models.ComponentSystem.objects.get(id=system1.id).doc_category_id == category1.id
        assert legacy_models.ComponentSystem.objects.get(id=system2.id).doc_category_id == category1.id
        assert legacy_models.ComponentSystem.objects.get(id=system3.id).doc_category_id == category1.id

        assert legacy_models.SystemDocCategory.objects.filter(id=category1.id).exists() is True
        assert legacy_models.SystemDocCategory.objects.filter(id=category2.id).exists() is False
