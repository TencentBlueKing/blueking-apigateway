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

from apigateway.biz.resource import find_resource_path_conflicts


@pytest.mark.parametrize("count", [199, 200, 201])
@pytest.mark.parametrize("single", [False, True])
@pytest.mark.parametrize("literal", [False, True])
def test_conflict_limit(count, single, literal):
    if single:
        resources = [{"id": index, "method": "GET", "path": f"/x/{{param_{index}}}"} for index in range(count)]
        candidate = {"method": "GET", "path": "/x/batch" if literal else "/x/{candidate}"}
    else:
        # Each distinct prefix contributes exactly one pair.
        resources = [
            {"id": index * 2 + side, "method": "GET", "path": f"/x/{index}/" + suffix}
            for index in range(count)
            for side, suffix in enumerate(["batch" if literal else "{left}", "{right}"])
        ]
        candidate = None
    conflicts, truncated = find_resource_path_conflicts(resources, candidate)
    assert len(conflicts) == min(count, 200)
    assert truncated is (count > 200)


def test_limit_ignores_pairs_with_different_methods():
    resources = [{"id": index, "method": "POST", "path": f"/x/{{p_{index}}}"} for index in range(201)]
    candidate = {"method": "GET", "path": "/x/{candidate}"}
    assert find_resource_path_conflicts(resources, candidate) == ([], False)
