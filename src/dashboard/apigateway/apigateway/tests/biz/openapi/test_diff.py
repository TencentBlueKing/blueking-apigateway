#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
# http://opensource.org/licenses/MIT
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
#
from copy import deepcopy

import pytest

from apigateway.biz.openapi import classify_resource_import_changes


def test_new_resource_is_add_without_comparison_queries(fake_gateway, fake_resource_data, django_assert_num_queries):
    assert fake_resource_data.resource is None
    with django_assert_num_queries(0):
        changes = classify_resource_import_changes(fake_gateway, [fake_resource_data])
    assert changes == {fake_resource_data.name: "add"}


@pytest.mark.parametrize("existing", [False, True])
def test_classification_does_not_modify_import_data(fake_gateway, fake_resource, fake_resource_data, existing):
    if existing:
        fake_resource_data.resource = fake_resource
    original = deepcopy(fake_resource_data.model_dump())
    classify_resource_import_changes(fake_gateway, [fake_resource_data])
    assert fake_resource_data.model_dump() == original
