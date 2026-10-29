# -*- coding: utf-8 -*-
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
import pytest

from apigateway.core.models import Schema


@pytest.mark.no_meta_schema
def test_pure_tests_do_not_implicitly_enable_database_access():
    with pytest.raises(RuntimeError, match="Database access not allowed"):
        Schema.objects.count()


@pytest.mark.no_meta_schema
@pytest.mark.django_db
def test_schema_opt_out_still_allows_explicit_database_access():
    schema = Schema.objects.create(name="explicit-schema", type="context", version="1", schema={"type": "object"})
    assert Schema.objects.get(id=schema.id).schema == {"type": "object"}
