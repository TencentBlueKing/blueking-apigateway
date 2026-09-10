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
from ddf import G

from apigateway.core.models import Gateway, Resource


def check(request_view, gateway, data=None):
    return request_view(
        method="GET" if data is None else "POST",
        view_name="resource.path_conflicts" if data is None else "resource.path_conflicts.check",
        path_params={"gateway_id": gateway.id},
        gateway=gateway,
        data=data or {},
    )


@pytest.mark.parametrize(
    "left,right,method,conflict_type",
    [
        ("/api/{bizId}/apps/{appId}", "/api/{bizI_d}/apps/{app_Id}", "GET", "normalized_path"),
        ("/api/{biz}/batch", "/api/{biz}/{set_id}", "DELETE", "literal_parameter"),
        ("/x/batch", "/x/{name}", "GET", "literal_parameter"),
        ("/x/{id}/", "/x/{name}", "GET", "normalized_path"),
        ("/x/{id}", "/x/{name}", "ANY", "normalized_path"),
        ("/x/{id}/a", "/x/{name}/b", "GET", None),
        ("/x/{id}/a", "/y/{name}/a", "GET", None),
        ("/x/{id}/a", "/x/{name}/a/b", "GET", None),
        ("/x/batch", "/x/other", "GET", None),
    ],
)
def test_all(request_view, fake_gateway, left, right, method, conflict_type):
    first = G(Resource, gateway=fake_gateway, method="GET" if method == "ANY" else method, path=left)
    second = G(Resource, gateway=fake_gateway, method=method, path=right)
    G(Resource, gateway=G(Gateway), method=method, path=left)
    response = check(request_view, fake_gateway)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["has_conflicts"] == bool(conflict_type)
    if conflict_type:
        assert len(data["conflicts"]) == 1
        conflict = data["conflicts"][0]
        assert conflict["type"] == conflict_type
        assert {item["id"] for item in conflict["resources"]} == {first.id, second.id}
    else:
        assert data["conflicts"] == []


def test_single_excludes_self_and_unrelated_conflicts(request_view, fake_gateway):
    resource = G(Resource, gateway=fake_gateway, method="GET", path="/x/{id}")
    G(Resource, gateway=fake_gateway, method="GET", path="/other/{id}")
    G(Resource, gateway=fake_gateway, method="GET", path="/other/{name}")
    response = check(request_view, fake_gateway, {"method": "GET", "path": "/x/{new_id}", "resource_id": resource.id})
    assert response.status_code == 200
    assert response.json()["data"] == {"has_conflicts": False, "conflicts": [], "truncated": False}
    response = check(request_view, fake_gateway, {"method": "GET", "path": "/x/{new_id}"})
    assert response.status_code == 200
    assert response.json()["data"]["has_conflicts"] is True
    assert Resource.objects.get(id=resource.id).path == "/x/{id}"


def test_different_methods(request_view, fake_gateway):
    G(Resource, gateway=fake_gateway, method="GET", path="/x/{id}")
    response = check(request_view, fake_gateway, {"method": "POST", "path": "/x/{name}"})
    assert response.json()["data"]["conflicts"] == []


@pytest.mark.parametrize(
    "data",
    [{}, {"method": "BAD", "path": "/x"}, {"method": "GET", "path": "x"}, {"method": "GET", "path": "/x/{123}"}],
)
def test_invalid_input(request_view, fake_gateway, data):
    assert check(request_view, fake_gateway, data).status_code == 400


def test_foreign_resource(request_view, fake_gateway):
    resource = G(Resource, gateway=G(Gateway))
    response = check(request_view, fake_gateway, {"method": "GET", "path": "/x", "resource_id": resource.id})
    assert response.status_code == 404


@pytest.mark.parametrize("path", ["/x/batch", "/x/{new_id}"])
def test_single_literal_parameter_pair(request_view, fake_gateway, path):
    G(Resource, gateway=fake_gateway, method="DELETE", path="/x/{id}")
    G(Resource, gateway=fake_gateway, method="DELETE", path="/x/batch")
    G(Resource, gateway=fake_gateway, method="DELETE", path="/unrelated/{id}")
    G(Resource, gateway=fake_gateway, method="DELETE", path="/unrelated/batch")
    response = check(request_view, fake_gateway, {"method": "DELETE", "path": path})
    conflicts = response.json()["data"]["conflicts"]
    assert {item["type"] for item in conflicts} == {"normalized_path", "literal_parameter"}
    assert len(conflicts) == 2
    assert all(any(resource["id"] is None for resource in item["resources"]) for item in conflicts)


def test_empty_gateway(request_view, fake_gateway):
    assert check(request_view, fake_gateway).json()["data"] == {
        "has_conflicts": False,
        "conflicts": [],
        "truncated": False,
    }


@pytest.mark.parametrize("single", [False, True])
def test_conflict_response_is_capped(request_view, fake_gateway, single):
    for index in range(201 if single else 21):
        G(Resource, gateway=fake_gateway, method="GET", path=f"/x/{{param_{index}}}")
    data = {"method": "GET", "path": "/x/{candidate}"} if single else None
    response = check(request_view, fake_gateway, data)
    assert response.status_code == 200
    result = response.json()["data"]
    assert len(result["conflicts"]) == 200
    assert result["has_conflicts"] is True
    assert result["truncated"] is True
