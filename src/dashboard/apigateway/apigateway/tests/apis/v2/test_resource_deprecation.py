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
from unittest import mock

import pytest

from apigateway.core.models import Resource, ResourceVersion


@pytest.fixture(autouse=True)
def clear_resource_version_cache():
    ResourceVersion.objects.get_resources.cache_clear()
    yield
    ResourceVersion.objects.get_resources.cache_clear()


@pytest.fixture
def deprecated_release(fake_released_resource, fake_resource_version):
    data = fake_released_resource.data
    data.update(is_public=True, is_deprecated=True, deprecated_note="Use v2")
    fake_released_resource.data = data
    fake_released_resource.is_public = True
    fake_released_resource.save()
    snapshots = fake_resource_version.data
    for item in snapshots:
        if item["id"] == fake_released_resource.resource_id:
            item.update(is_public=True, is_deprecated=True, deprecated_note="Use v2")
    fake_resource_version.data = snapshots
    fake_resource_version.save()
    Resource.objects.filter(pk=fake_released_resource.resource_id).update(is_deprecated=False)
    return fake_released_resource


@pytest.mark.parametrize("historical", [False, True])
@pytest.mark.parametrize(
    "view",
    [
        "openapi.v2.inner.gateway.released_resource.list",
        "openapi.v2.inner.gateway.released_resource.lookup",
        "openapi.v2.open.gateway.resources.detail",
        "openapi.v2.open.gateway.released_resources.list",
        "openapi.v2.open.gateway.released_resources.retrieve",
        "openapi.released.stage_resources_by_gateway_name",
        "openapi.released.resources.detail_by_gateway_name",
    ],
)
def test_published_resource_deprecation(
    request_view,
    fake_gateway,
    fake_stage,
    fake_resource_version,
    deprecated_release,
    view,
    historical,
):
    if historical:
        data = deprecated_release.data
        data.pop("is_deprecated")
        data.pop("deprecated_note")
        deprecated_release.data = data
        deprecated_release.save()
        snapshots = fake_resource_version.data
        for item in snapshots:
            item.pop("is_deprecated", None)
            item.pop("deprecated_note", None)
        fake_resource_version.data = snapshots
        fake_resource_version.save()

    params = {"gateway_name": fake_gateway.name}
    query = {}
    if "inner" in view:
        query["fields"] = "id,name,is_deprecated,deprecated_note"
        if view.endswith("lookup"):
            query["names"] = deprecated_release.resource_name
    elif view.endswith("resources.detail"):
        params["resource_name"] = deprecated_release.resource_name
        query["stage_name"] = fake_stage.name
    else:
        params["stage_name"] = fake_stage.name
        if view.endswith("retrieve") or "detail_by_gateway_name" in view:
            params["resource_name"] = deprecated_release.resource_name

    response = request_view(
        method="GET",
        view_name=view,
        path_params=params,
        gateway=fake_gateway,
        app=mock.MagicMock(app_code="bk_auth"),
        data=query,
    )
    assert response.status_code == 200, response.json()
    data = response.json()["data"]
    if isinstance(data, dict) and "results" in data:
        data = data["results"]
    if isinstance(data, list):
        data = next(item for item in data if item["id"] == deprecated_release.resource_id)
    assert (data["is_deprecated"], data["deprecated_note"]) == ((False, "") if historical else (True, "Use v2"))
    assert "deprecated_notes" not in data
    if view == "openapi.v2.open.gateway.resources.detail":
        assert (data["doc"]["is_deprecated"], data["doc"]["deprecated_note"]) == (
            (False, "") if historical else (True, "Use v2")
        )


def test_open_editable_resource_list_selects_deprecation(request_view, fake_resource):
    fake_resource.is_deprecated = True
    fake_resource.is_public = True
    fake_resource.save()
    response = request_view(
        method="GET",
        view_name="openapi.v2.open.gateway.resources.list",
        path_params={"gateway_name": fake_resource.gateway.name},
        gateway=fake_resource.gateway,
        app=mock.MagicMock(app_code="bk_auth"),
        data={"fields": "id,is_deprecated,deprecated_note"},
    )
    assert response.status_code == 200, response.json()
    item = next(item for item in response.json()["data"] if item["id"] == fake_resource.id)
    assert item == {"id": fake_resource.id, "is_deprecated": True, "deprecated_note": ""}
