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
@pytest.mark.parametrize("literal", [False, True])
def test_conflict_group_limit(count, literal):
    resources = [
        {"id": index * 2 + side, "method": "GET", "path": f"/x/{index}/" + suffix}
        for index in range(count)
        for side, suffix in enumerate(["batch" if literal else "{left}", "{right}"])
    ]
    groups, truncated = find_resource_path_conflicts(resources)
    assert len(groups) == min(count, 200)
    assert truncated is (count > 200)


@pytest.mark.parametrize("single", [False, True])
def test_dense_resources_form_one_group(single):
    resources = [{"id": index, "method": "GET", "path": f"/x/{{p{index}}}"} for index in range(2000)]
    candidate = resources.pop() if single else None
    groups, truncated = find_resource_path_conflicts(resources, candidate)
    assert truncated is False
    assert len(groups) == 1
    assert groups[0]["method"] == "GET"
    assert len(groups[0]["resources"]) == 2000
    assert {item["id"] for item in groups[0]["resources"]} == set(range(2000))


@pytest.mark.parametrize("single", [False, True])
@pytest.mark.parametrize("literal", [False, True])
def test_any_expands_without_mixing_concrete_methods(single, literal):
    resources = [
        {"id": 1, "method": "GET", "path": "/x/batch" if literal else "/x/{get}"},
        {"id": 2, "method": "POST", "path": "/x/batch" if literal else "/x/{post}"},
    ]
    candidate = {"id": 3, "method": "ANY", "path": "/x/{any}"}
    if not single:
        resources.append(candidate)
        candidate = None
    groups, truncated = find_resource_path_conflicts(resources, candidate)
    assert truncated is False
    assert {group["method"]: {item["id"] for item in group["resources"]} for group in groups} == {
        "GET": {1, 3},
        "POST": {2, 3},
    }
    assert all(item["method"] == "ANY" for group in groups for item in group["resources"] if item["id"] == 3)


@pytest.mark.parametrize("single", [False, True])
def test_any_against_any_has_one_group_per_method(single):
    resources = [{"id": 1, "method": "ANY", "path": "/x/{first}"}]
    candidate = {"id": 2, "method": "ANY", "path": "/x/{second}"}
    if not single:
        resources.append(candidate)
        candidate = None
    groups, truncated = find_resource_path_conflicts(resources, candidate)
    assert truncated is False
    assert len(groups) == 7
    assert {group["method"] for group in groups} == {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
    assert all(len(group["resources"]) == 2 for group in groups)


def test_literal_candidate_only_returns_overlapping_resources():
    resources = [
        {"id": 1, "method": "GET", "path": "/x/batch"},
        {"id": 2, "method": "GET", "path": "/x/other"},
        {"id": 3, "method": "GET", "path": "/x/{id}"},
    ]
    candidate = {"id": 4, "method": "GET", "path": "/x/batch"}
    groups, truncated = find_resource_path_conflicts(resources, candidate)
    assert truncated is False
    assert {group["type"]: {item["id"] for item in group["resources"]} for group in groups} == {
        "normalized_path": {1, 4},
        "literal_parameter": {3, 4},
    }


def test_different_methods_do_not_conflict():
    resources = [{"id": index, "method": "POST", "path": f"/x/{{p{index}}}"} for index in range(201)]
    candidate = {"method": "GET", "path": "/x/{candidate}"}
    assert find_resource_path_conflicts(resources, candidate) == ([], False)
