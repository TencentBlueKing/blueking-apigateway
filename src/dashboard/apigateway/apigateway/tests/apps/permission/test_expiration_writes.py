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

import datetime

import pytest
from ddf import G
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connection
from django.test import RequestFactory
from django.utils import timezone

from apigateway.apps.permission.models import AppGatewayPermission, AppResourcePermission
from apigateway.biz.permission import ResourcePermissionHandler
from apigateway.core.models import Gateway, Resource
from apigateway.utils.time import NeverExpiresTime

pytestmark = pytest.mark.django_db


def make_permission(model, gateway, app_code, expires):
    fields = {"gateway": gateway, "bk_app_code": app_code, "grant_type": "initialize", "expires": expires}
    if model is AppResourcePermission:
        fields["resource_id"] = G(Resource, gateway=gateway).id
    permission = model.objects.create(**fields)
    if expires is None:
        table = connection.ops.quote_name(model._meta.db_table)
        with connection.cursor() as cursor:
            cursor.execute(f"UPDATE {table} SET expires = NULL WHERE id = %s", [permission.pk])
        permission.refresh_from_db()
    return permission


@pytest.mark.parametrize("model", [AppGatewayPermission, AppResourcePermission])
@pytest.mark.parametrize("change", [False, True], ids=["add", "change"])
def test_admin_blank_expiration_is_stored_as_permanent(model, change):
    gateway = G(Gateway)
    request = RequestFactory().get("/")
    request.user = G(User, is_superuser=True, is_staff=True)
    model_admin = admin.site._registry[model]
    permission = make_permission(model, gateway, "admin-app", timezone.now()) if change else None
    form_class = model_admin.get_form(request, obj=permission)
    data = {
        "gateway": gateway.pk,
        "bk_app_code": "admin-app",
        "grant_type": "initialize",
        "expires_0": "",
        "expires_1": "",
    }
    if model is AppResourcePermission:
        data["resource_id"] = permission.resource_id if permission else G(Resource, gateway=gateway).id
    form = form_class(data=data, instance=permission)
    assert form.is_valid(), form.errors
    permission = form.save(commit=False)
    model_admin.save_model(request, permission, form, change)
    permission.refresh_from_db()
    assert permission.expires == NeverExpiresTime.time


@pytest.mark.parametrize("model", [AppGatewayPermission, AppResourcePermission])
@pytest.mark.parametrize(
    "source_null,destination",
    [(True, "missing"), (True, "finite"), (True, "null"), (False, "null"), (False, "finite")],
)
def test_copy_permission_preserves_permanent_semantics(model, source_null, destination):
    gateway = G(Gateway)
    finite = timezone.now() + datetime.timedelta(days=30)
    source = make_permission(model, gateway, "source-app", None if source_null else finite)
    fields = {"gateway": gateway, "bk_app_code": "destination-app"}
    if model is AppResourcePermission:
        fields["resource_id"] = source.resource_id
    if destination != "missing":
        target = model.objects.create(**fields, grant_type="initialize", expires=finite - datetime.timedelta(days=1))
        if destination == "null":
            table = connection.ops.quote_name(model._meta.db_table)
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE {table} SET expires = NULL WHERE id = %s", [target.pk])
    call_command("copy_app_permission", src_app="source-app", dst_app="destination-app", dry_run=True)
    call_command("copy_app_permission", src_app="source-app", dst_app="destination-app", dry_run=False)
    call_command("copy_app_permission", src_app="source-app", dst_app="destination-app", dry_run=False)
    target = model.objects.get(**fields)
    expected = None if destination == "null" else NeverExpiresTime.time if source_null else finite
    assert target.expires == expected
    source.refresh_from_db()
    assert source.expires == (None if source_null else finite)


@pytest.mark.parametrize("expires", [None, NeverExpiresTime.time, "finite"])
def test_sync_resource_permission_normalizes_legacy_null_without_rewriting_source(expires):
    gateway = G(Gateway)
    expires = timezone.now() + datetime.timedelta(days=10) if expires == "finite" else expires
    source = make_permission(AppGatewayPermission, gateway, "sync-app", expires)
    resource = G(Resource, gateway=gateway)
    existing = make_permission(AppResourcePermission, gateway, "sync-app", None)
    ResourcePermissionHandler.sync_from_gateway_permission(gateway, "sync-app", [resource.id, existing.resource_id])
    target = AppResourcePermission.objects.get(gateway=gateway, bk_app_code="sync-app", resource_id=resource.id)
    assert target.expires == (NeverExpiresTime.time if expires is None else expires)
    assert target.grant_type == "sync"
    existing.refresh_from_db()
    source.refresh_from_db()
    assert existing.expires is None
    assert source.expires == expires
