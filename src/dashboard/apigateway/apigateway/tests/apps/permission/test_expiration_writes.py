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
import json
from io import StringIO

import pytest
from django.contrib import admin
from django.core.management import call_command
from django.db import connection, models
from django.utils import timezone

from apigateway.apps.permission.models import AppGatewayPermission, AppResourcePermission
from apigateway.utils.time import NeverExpiresTime

pytestmark = pytest.mark.django_db


@pytest.fixture(params=[AppGatewayPermission, AppResourcePermission], ids=["gateway", "resource"])
def permission_input(request, fake_resource):
    model = request.param
    fields = {"gateway": fake_resource.gateway, "bk_app_code": "test-app", "grant_type": "initialize"}
    if model is AppResourcePermission:
        fields["resource_id"] = fake_resource.id
    return model, fields


@pytest.mark.parametrize("writer", ["create", "bulk_create", "update", "expression_update", "bulk_update", "upsert"])
def test_null_expiration_is_written_as_permanent(permission_input, writer):
    model, fields = permission_input
    if writer == "create":
        record = model.objects.create(**fields, expires=None)
        assert record.expires == NeverExpiresTime.time
    elif writer == "bulk_create":
        model.objects.bulk_create([model(**fields, expires=None)])
    else:
        record = model.objects.create(**fields)
        if writer == "update":
            model.objects.filter(pk=record.pk).update(expires=None)
        elif writer == "expression_update":
            model.objects.filter(pk=record.pk).update(expires=models.Value(None))
        elif writer == "bulk_update":
            record.expires = None
            model.objects.bulk_update([record], ["expires"])
        else:
            model.objects.update_or_create(pk=record.pk, defaults={"expires": None})

    assert model.objects.get(**fields).expires == NeverExpiresTime.time


def test_omitted_and_finite_expirations_are_preserved(permission_input):
    model, fields = permission_input
    before = timezone.now()
    record = model.objects.create(**fields)
    record.refresh_from_db()
    assert before + datetime.timedelta(days=180) <= record.expires <= timezone.now() + datetime.timedelta(days=180)

    finite = datetime.datetime(2030, 3, 4, tzinfo=datetime.UTC)
    record.expires = finite
    record.save(update_fields=["expires"])
    record.refresh_from_db()
    assert record.expires == finite


@pytest.fixture
def legacy_null_permission(permission_input):
    model, fields = permission_input
    record = model.objects.create(**fields)
    table = connection.ops.quote_name(model._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE {table} SET expires = NULL WHERE id = %s", [record.pk])

    record.refresh_from_db()
    return record


def test_partial_save_preserves_legacy_null_expiration(legacy_null_permission):
    record = legacy_null_permission
    record.handled_by = "operator"
    record.save(update_fields=["handled_by"])
    record.refresh_from_db()
    assert record.handled_by == "operator"
    assert record.expires is None


def test_admin_can_save_blank_expiration(permission_input, rf, django_user_model):
    model, fields = permission_input
    request = rf.post("/")
    request.user = django_user_model(is_superuser=True, is_staff=True)
    model_admin = admin.site.get_model_admin(model)
    form = model_admin.get_form(request)(
        data={**fields, "gateway": fields["gateway"].pk, "expires_0": "", "expires_1": ""}
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["expires"] is None
    record = form.save(commit=False)
    model_admin.save_model(request, record, form, change=False)
    record.refresh_from_db()
    assert record.expires == NeverExpiresTime.time


def test_loaddata_can_restore_null_as_permanent(permission_input, tmp_path):
    model, fields = permission_input
    fixture = tmp_path / "permissions.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "model": model._meta.label_lower,
                    "fields": {**fields, "gateway": fields["gateway"].pk, "expires": None},
                }
            ]
        )
    )
    call_command("loaddata", str(fixture), verbosity=0)
    assert model.objects.get(**fields).expires == NeverExpiresTime.time


def test_permission_import_distinguishes_null_from_invalid_expiration(permission_input, fake_resource, tmp_path):
    model, fields = permission_input
    finite = datetime.datetime(2030, 3, 4, tzinfo=datetime.UTC)
    model.objects.create(**fields, expires=finite)
    resource_name = fake_resource.name if model is AppResourcePermission else "*"
    common = {"gateway_name": fields["gateway"].name, "resource_name": resource_name}
    imports = [
        {**common, "bk_app_code": fields["bk_app_code"]},
        {**common, "bk_app_code": fields["bk_app_code"], "expires": ""},
        {**common, "bk_app_code": fields["bk_app_code"], "expires": False},
        {**common, "bk_app_code": fields["bk_app_code"], "expires": "2040-02-31T00:00:00Z"},
        {**common, "bk_app_code": "permanent-app", "expires": None},
        {**common, "bk_app_code": "finite-app", "expires": finite.isoformat()},
    ]
    backup = tmp_path / "permissions.json"
    backup.write_text(json.dumps(imports))
    errors = StringIO()
    call_command("permission_export_import", "import", file=str(backup), stderr=errors, stdout=StringIO())
    assert errors.getvalue().count("skip") == 4
    assert model.objects.get(**fields).expires == finite
    assert model.objects.get(gateway=fields["gateway"], bk_app_code="permanent-app").expires == NeverExpiresTime.time
    assert model.objects.get(gateway=fields["gateway"], bk_app_code="finite-app").expires == finite


def test_copy_legacy_permission_can_be_repeated(permission_input, legacy_null_permission):
    model, fields = permission_input
    for _ in range(2):
        call_command("copy_app_permission", src_app=fields["bk_app_code"], dst_app="destination")
    assert model.objects.get(gateway=fields["gateway"], bk_app_code="destination").expires == NeverExpiresTime.time
    legacy_null_permission.refresh_from_db()
    assert legacy_null_permission.expires is None
