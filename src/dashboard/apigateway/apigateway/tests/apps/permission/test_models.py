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
from django.db import connection
from django.utils import timezone

from apigateway.apps.permission.models import AppGatewayPermission, AppPermissionRecord, AppResourcePermission
from apigateway.core.models import Gateway, Resource
from apigateway.utils.time import NeverExpiresTime


@pytest.fixture(params=[AppGatewayPermission, AppResourcePermission])
def permission_fields(request):
    gateway = G(Gateway)
    fields = {"gateway": gateway, "bk_app_code": "test-app", "grant_type": "initialize"}
    if request.param is AppResourcePermission:
        fields["resource_id"] = G(Resource, gateway=gateway).id
    return request.param, fields


def set_legacy_null(permission):
    # Direct SQL represents data written before Dashboard normalized expiration.
    table = connection.ops.quote_name(permission._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE {table} SET expires = NULL WHERE id = %s", [permission.pk])
    permission.refresh_from_db()
    assert permission.expires is None


@pytest.mark.django_db
@pytest.mark.parametrize("writer", ["create", "save", "get_or_create", "update_or_create", "bulk_create"])
def test_new_null_expiration_is_stored_as_permanent(permission_fields, writer):
    model, fields = permission_fields
    if writer == "create":
        permission = model.objects.create(**fields, expires=None)
    elif writer == "save":
        permission = model(**fields, expires=None)
        permission.save()
    elif writer in {"get_or_create", "update_or_create"}:
        permission, _ = getattr(model.objects, writer)(**fields, defaults={"expires": None})
    else:
        permission = model(**fields, expires=None)
        model.objects.bulk_create([permission])
    permission.refresh_from_db()
    assert permission.expires == NeverExpiresTime.time
    assert permission.expires_in is None


@pytest.mark.django_db
@pytest.mark.parametrize("writer", ["save", "full_save", "update", "update_or_create", "bulk_update"])
def test_explicit_null_expiration_update_is_stored_as_permanent(permission_fields, writer):
    model, fields = permission_fields
    permission = model.objects.create(**fields, expires=timezone.now())
    permission.expires = None
    if writer == "save":
        permission.save(update_fields=["expires"])
    elif writer == "full_save":
        permission.save()
    elif writer == "update":
        model.objects.filter(pk=permission.pk).update(expires=None)
    elif writer == "update_or_create":
        model.objects.update_or_create(**fields, defaults={"expires": None})
    else:
        model.objects.bulk_update([permission], ["expires"])
    permission.refresh_from_db()
    assert permission.expires == NeverExpiresTime.time


@pytest.mark.django_db
@pytest.mark.parametrize("writer", ["save", "update", "bulk_update", "update_or_create", "deferred_save"])
def test_unrelated_update_preserves_legacy_null(permission_fields, writer):
    model, fields = permission_fields
    permission = model.objects.create(**fields)
    set_legacy_null(permission)
    permission.handled_by = "operator"
    if writer == "save":
        permission.save(update_fields=["handled_by"])
    elif writer == "update":
        model.objects.filter(pk=permission.pk).update(handled_by="operator")
    elif writer == "bulk_update":
        model.objects.bulk_update([permission], ["handled_by"])
    elif writer == "update_or_create":
        model.objects.update_or_create(**fields, defaults={"handled_by": "operator"})
    else:
        deferred = model.objects.only("id", "handled_by").get(pk=permission.pk)
        deferred.handled_by = "operator"
        deferred.save()
    permission.refresh_from_db()
    assert permission.expires is None
    assert permission.handled_by == "operator"


@pytest.mark.django_db
def test_omitted_expiration_keeps_default_and_finite_expiration_is_unchanged(permission_fields, mocker):
    model, fields = permission_fields
    now = timezone.now()
    mocker.patch("django.utils.timezone.now", return_value=now)
    permission = model.objects.create(**fields)
    permission.refresh_from_db()
    assert permission.expires == now + datetime.timedelta(days=180)
    permission.expires = now + datetime.timedelta(days=10)
    permission.save(update_fields=["expires"])
    permission.refresh_from_db()
    assert permission.expires == now + datetime.timedelta(days=10)


class TestAppPermissionRecord:
    def test_applied_by_id_index(self):
        assert any(
            index.fields == ["applied_by", "id"] and index.name == "perm_record_applied_by_id_idx"
            for index in AppPermissionRecord._meta.indexes
        )


@pytest.mark.django_db
def test_bulk_writes_preserve_finite_expiration_and_accept_iterables(permission_fields):
    model, fields = permission_fields
    finite = timezone.now() + datetime.timedelta(days=10)
    permanent = model(**fields, expires=None)
    finite_permission = model(**{**fields, "bk_app_code": "finite-app"}, expires=finite)
    model.objects.bulk_create(iter([permanent, finite_permission]))
    permanent.refresh_from_db()
    finite_permission.refresh_from_db()
    assert permanent.expires == NeverExpiresTime.time
    assert finite_permission.expires == finite
    permanent.expires = None
    finite_permission.expires = finite + datetime.timedelta(days=1)
    model.objects.bulk_update(iter([permanent, finite_permission]), iter(["expires"]), batch_size=1)
    permanent.refresh_from_db()
    finite_permission.refresh_from_db()
    assert permanent.expires == NeverExpiresTime.time
    assert finite_permission.expires == finite + datetime.timedelta(days=1)


@pytest.mark.django_db
def test_update_or_create_separates_creation_defaults_and_updates_audit_time(permission_fields, mocker):
    model, fields = permission_fields
    start = timezone.now()
    mocker.patch("django.utils.timezone.now", return_value=start)
    permission, created = model.objects.update_or_create(
        **fields, defaults={"expires": lambda: start}, create_defaults={"expires": lambda: None}
    )
    assert created
    permission.refresh_from_db()
    assert permission.expires == NeverExpiresTime.time
    assert permission.created_time == start
    set_legacy_null(permission)
    later = start + datetime.timedelta(days=1)
    mocker.patch("django.utils.timezone.now", return_value=later)
    permission, created = model.objects.update_or_create(
        **fields, defaults={"handled_by": lambda: "operator"}, create_defaults={"expires": start}
    )
    assert not created
    permission.refresh_from_db()
    assert permission.expires is None
    assert permission.handled_by == "operator"
    assert permission.created_time == start
    assert permission.updated_time == later
    permission, created = model.objects.update_or_create(**fields, defaults={"expires": lambda: later})
    assert not created
    permission.refresh_from_db()
    assert permission.expires == later
