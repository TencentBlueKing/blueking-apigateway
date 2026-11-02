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
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from ddf import G
from django.urls import resolve, reverse

from apigateway.apis.permissions import GatewayActionPermission
from apigateway.apps.rbac.models import GatewayMember
from apigateway.biz.resource import ResourcesSaver
from apigateway.biz.resource_version import ResourceDifferHandler, ResourceVersionHandler
from apigateway.core.models import Backend, Release, Resource, ResourceVersion, Stage
from apigateway.service.resource import snapshot_resource


def set_deprecation(request_view, resource, **data):
    return request_view(
        method="PATCH",
        view_name="resource.deprecation.update",
        path_params={"gateway_id": resource.gateway_id, "resource_id": resource.id},
        gateway=resource.gateway,
        data=data,
    )


def test_deprecation_is_narrow_and_idempotent(request_view, fake_resource, mocker):
    before = deepcopy(fake_resource.__dict__)
    audit = mocker.patch("apigateway.apis.web.resource.views.Auditor.record_resource_op_success")
    for deprecated, notes in [(True, "Use v2"), (True, "Use v3"), (False, "clear me")]:
        response = set_deprecation(request_view, fake_resource, is_deprecated=deprecated, deprecated_notes=notes)
        assert response.status_code == 204
        fake_resource.refresh_from_db()
        assert fake_resource.is_deprecated is deprecated
        assert fake_resource.deprecated_notes == (notes if deprecated else "")
        for key, value in before.items():
            if key not in {"_state", "is_deprecated", "deprecated_notes", "updated_time", "updated_by"}:
                assert getattr(fake_resource, key) == value
    assert audit.call_count == 3
    assert audit.call_args.kwargs["data_before"]["is_deprecated"] is True
    assert audit.call_args.kwargs["data_after"]["is_deprecated"] is False
    updated = fake_resource.updated_time
    assert set_deprecation(request_view, fake_resource, is_deprecated=False).status_code == 204
    fake_resource.refresh_from_db()
    assert fake_resource.updated_time == updated
    assert audit.call_count == 3


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"is_deprecated": None},
        {"is_deprecated": "true"},
        {"is_deprecated": True, "deprecated_notes": None},
        {"is_deprecated": True, "deprecated_notes": 123},
        {"is_deprecated": True, "deprecated_notes": "x" * 2049},
    ],
)
def test_deprecation_rejects_invalid_input(request_view, fake_resource, data):
    assert set_deprecation(request_view, fake_resource, **data).status_code == 400


def test_deprecation_rejects_foreign_resource(request_view, fake_resource, fake_gateway):
    other = G(Resource)
    response = request_view(
        method="PATCH",
        view_name="resource.deprecation.update",
        path_params={"gateway_id": fake_gateway.id, "resource_id": other.id},
        gateway=fake_gateway,
        data={"is_deprecated": True},
    )
    assert response.status_code == 404


@pytest.mark.parametrize("role,allowed", [("administrator", True), ("operator", False), (None, False)])
def test_deprecation_requires_manage_gateway(fake_gateway, fake_request, role, allowed, mocker):
    mocker.patch("apigateway.apis.permissions.is_iam_auth_active", return_value=False)
    username = "deprecation_user"
    if role:
        G(GatewayMember, gateway=fake_gateway, username=username, role=role)
    fake_request.user = SimpleNamespace(username=username)
    fake_request.method = "PATCH"
    match = resolve(reverse("resource.deprecation.update", kwargs={"gateway_id": fake_gateway.id, "resource_id": 1}))
    view = match.func.view_class()
    view.kwargs = match.kwargs
    assert GatewayActionPermission().has_permission(fake_request, view) is allowed


def test_normal_saver_preserves_concurrently_updated_deprecation(fake_resource, fake_resource_data):
    data = fake_resource_data.model_copy(update={"resource": fake_resource})
    Resource.objects.filter(pk=fake_resource.pk).update(is_deprecated=True, deprecated_notes="Use v2")
    ResourcesSaver(fake_resource.gateway, [data], "admin")._save_resources()
    fake_resource.refresh_from_db()
    assert fake_resource.is_deprecated is True
    assert fake_resource.deprecated_notes == "Use v2"


def test_saver_mixed_explicit_and_omitted_deprecation(fake_resource, fake_resource_data):
    Resource.objects.filter(pk=fake_resource.pk).update(is_deprecated=True, deprecated_notes="Keep")
    other = G(Resource, gateway=fake_resource.gateway, is_deprecated=True, deprecated_notes="Clear")
    omitted = fake_resource_data.model_copy(update={"resource": fake_resource})
    explicit = fake_resource_data.model_copy(
        update={"resource": other, "is_deprecated": False, "deprecated_notes": ""}
    )
    ResourcesSaver(fake_resource.gateway, [omitted, explicit], "admin")._save_resources()
    fake_resource.refresh_from_db()
    other.refresh_from_db()
    assert (fake_resource.is_deprecated, fake_resource.deprecated_notes) == (True, "Keep")
    assert (other.is_deprecated, other.deprecated_notes) == (False, "")


def test_doc_deprecation_follows_environment_version(request_view, fake_gateway, fake_resource, fake_stage):
    fake_resource.is_public = True
    fake_resource.is_deprecated = False
    fake_resource.save()
    old = G(ResourceVersion, gateway=fake_gateway, _data=json.dumps(ResourceVersionHandler.make_version(fake_gateway)))
    release = G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=old)
    other_stage = G(Stage, gateway=fake_gateway, name="other")
    G(Release, gateway=fake_gateway, stage=other_stage, resource_version=old)

    def read(stage):
        response = request_view(
            method="GET",
            view_name="docs.gateway.resource.list",
            path_params={"gateway_name": fake_gateway.name},
            gateway=fake_gateway,
            data={"stage_name": stage.name},
        )
        assert response.status_code == 200
        return next(item for item in response.json()["data"] if item["id"] == fake_resource.id)

    assert (
        set_deprecation(request_view, fake_resource, is_deprecated=True, deprecated_notes="Use v2").status_code == 204
    )
    new = G(ResourceVersion, gateway=fake_gateway, _data=json.dumps(ResourceVersionHandler.make_version(fake_gateway)))
    assert read(fake_stage)["is_deprecated"] is False
    release.resource_version = new
    release.save()
    assert read(fake_stage)["is_deprecated"] is True
    assert read(fake_stage)["deprecated_notes"] == "Use v2"
    assert read(other_stage)["is_deprecated"] is False
    # Historical versions remain readable with missing fields.
    data = old.data
    for item in data:
        item.pop("is_deprecated", None)
        item.pop("deprecated_notes", None)
    old.data = data
    old.save()
    release.resource_version = old
    release.save()
    assert read(fake_stage)["is_deprecated"] is False
    assert read(fake_stage)["deprecated_notes"] == ""


@pytest.mark.parametrize("version", ["2.0", "3.0.3", "3.1.0"])
def test_sync_deprecation_without_doc_generation(request_view, fake_gateway, mocker, version):
    mocker.patch(
        "apigateway.apis.v2.permissions.OpenAPIV2GatewayRelatedAppPermission.has_permission", return_value=True
    )
    G(Backend, gateway=fake_gateway, name="default")
    operation = {
        "operationId": "get_users",
        "deprecated": True,
        "x-bk-apigateway-resource": {"deprecatedNotes": "Use v2"},
        "responses": {"200": {"description": "OK"}},
    }
    spec = {
        ("swagger" if version == "2.0" else "openapi"): version,
        "info": {"title": "test", "version": "1"},
        "paths": {"/users": {"get": operation}},
    }

    def sync():
        return request_view(
            method="POST",
            view_name="openapi.v2.sync.gateway.resources.sync",
            path_params={"gateway_name": fake_gateway.name},
            gateway=fake_gateway,
            data={"content": json.dumps(spec)},
        )

    response = sync()
    assert response.status_code == 200, response.json()
    resource = Resource.objects.get(gateway=fake_gateway, name="get_users")
    assert (resource.is_deprecated, resource.deprecated_notes) == (True, "Use v2")
    assert snapshot_resource(resource, as_dict=True)["is_deprecated"] is True
    operation.pop("deprecated")
    operation["x-bk-apigateway-resource"].pop("deprecatedNotes")
    assert sync().status_code == 200
    resource.refresh_from_db()
    assert (resource.is_deprecated, resource.deprecated_notes) == (False, "")
    operation["deprecated"] = True
    operation["x-bk-apigateway-resource"]["deprecatedNotes"] = "x" * 2049
    assert sync().status_code == 400
    resource.refresh_from_db()
    assert resource.is_deprecated is False


@pytest.mark.parametrize("create", [False, True])
def test_regular_write_does_not_accept_deprecation(request_view, fake_resource, create):
    fake_resource.is_deprecated = True
    fake_resource.deprecated_notes = "Keep"
    fake_resource.save()
    backend = Backend.objects.filter(gateway=fake_resource.gateway).first()
    data = {
        "name": "normal_resource",
        "description": "changed",
        "is_public": True,
        "method": "GET",
        "path": "/normal/",
        "label_ids": [],
        "backend": {"id": backend.id, "config": {"method": "GET", "path": "/normal/", "timeout": 30}},
        "auth_config": {"auth_verified_required": True, "app_verified_required": True, "resource_perm_required": True},
        "is_deprecated": create,
        "deprecated_notes": "Must be ignored",
    }
    path_params = {"gateway_id": fake_resource.gateway_id}
    if not create:
        path_params["id"] = fake_resource.id
    response = request_view(
        method="POST" if create else "PUT",
        view_name="resource.list_create" if create else "resource.retrieve_update_destroy",
        path_params=path_params,
        gateway=fake_resource.gateway,
        data=data,
    )
    assert response.status_code == (201 if create else 204), response.json()
    resource = Resource.objects.get(gateway=fake_resource.gateway, name="normal_resource")
    assert (resource.is_deprecated, resource.deprecated_notes) == ((False, "") if create else (True, "Keep"))


def test_deprecation_diff_and_management_responses(request_view, fake_resource):
    before = snapshot_resource(fake_resource, as_dict=True)
    assert (
        set_deprecation(request_view, fake_resource, is_deprecated=True, deprecated_notes="Use v2").status_code == 204
    )
    fake_resource.refresh_from_db()
    after = snapshot_resource(fake_resource, as_dict=True)
    for source, target in [(before, after), (after, before)]:
        result = ResourceDifferHandler.diff_resource_version_data([deepcopy(source)], [deepcopy(target)], {}, {})
        assert result["update"][0]["target"]["diff"]["is_deprecated"] is target["is_deprecated"]
        assert result["update"][0]["target"]["diff"]["deprecated_notes"] == target["deprecated_notes"]
    # Read APIs expose metadata independently of the regular input contract.
    for view, params in [
        ("resource.list_create", {"gateway_id": fake_resource.gateway_id}),
        ("resource.retrieve_update_destroy", {"gateway_id": fake_resource.gateway_id, "id": fake_resource.id}),
    ]:
        response = request_view(method="GET", view_name=view, path_params=params, gateway=fake_resource.gateway)
        result = response.json()["data"]
        if "results" in result:
            result = next(item for item in result["results"] if item["id"] == fake_resource.id)
        assert (result["is_deprecated"], result["deprecated_notes"]) == (True, "Use v2")


def test_label_edit_preserves_concurrently_updated_deprecation(request_view, fake_resource, mocker):
    mocker.patch("apigateway.apis.web.resource.views.ResourceLabelUpdateApi.get_object", return_value=fake_resource)
    Resource.objects.filter(pk=fake_resource.pk).update(is_deprecated=True, deprecated_notes="Use v2")
    response = request_view(
        method="PUT",
        view_name="resource.label.update",
        path_params={"gateway_id": fake_resource.gateway_id, "resource_id": fake_resource.id},
        gateway=fake_resource.gateway,
        data={"label_ids": []},
    )
    assert response.status_code == 204
    fake_resource.refresh_from_db()
    assert (fake_resource.is_deprecated, fake_resource.deprecated_notes) == (True, "Use v2")
