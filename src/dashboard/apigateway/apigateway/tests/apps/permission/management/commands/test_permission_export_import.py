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
from ddf import G
from django.core.management import call_command
from django.db import connection
from django.utils import timezone

from apigateway.apps.permission.constants import GrantTypeEnum
from apigateway.apps.permission.models import AppGatewayPermission, AppResourcePermission
from apigateway.core.models import Gateway, Resource
from apigateway.utils.time import NeverExpiresTime

pytestmark = pytest.mark.django_db

COMMAND_NAME = "permission_export_import"
PERMISSION_MODELS = [AppGatewayPermission, AppResourcePermission]


def make_permission(permission_model, **fields):
    permission = G(permission_model, **fields)
    if fields.get("expires") is None:
        # Preserve coverage of historical NULL rows without using normalized Dashboard writes.
        table = connection.ops.quote_name(permission_model._meta.db_table)
        with connection.cursor() as cursor:
            cursor.execute(f"UPDATE {table} SET expires = NULL WHERE id = %s", [permission.pk])
    return permission


@pytest.mark.parametrize("permission_model", PERMISSION_MODELS)
@pytest.mark.parametrize("explicit_cutoff", [False, True], ids=["default-cutoff", "explicit-cutoff"])
def test_export_import_preserves_active_permissions(permission_model, explicit_cutoff, tmp_path, mocker):
    now = timezone.make_aware(datetime.datetime(2026, 1, 19, 11, 0, 0))
    mocker.patch("django.utils.timezone.now", return_value=now)
    cutoff = now + datetime.timedelta(days=1) if explicit_cutoff else now
    gateway = G(Gateway, name="source-gateway")
    resource = G(Resource, gateway=gateway, name="shared-resource")
    permission_fields = {"resource_id": resource.id} if permission_model is AppResourcePermission else {}
    active_expirations = {
        "future-app": cutoff + datetime.timedelta(days=30),
        "permanent-app": None,
        "sentinel-app": NeverExpiresTime.time,
    }
    expirations = {
        **active_expirations,
        "expired-app": now - datetime.timedelta(seconds=1),
        "cutoff-app": cutoff,
    }
    for app_code, expires in expirations.items():
        make_permission(permission_model, gateway=gateway, bk_app_code=app_code, expires=expires, **permission_fields)

    file_path = tmp_path / "permissions.json"
    export_options = {"expire_datetime": cutoff.strftime("%Y-%m-%d %H:%M:%S")} if explicit_cutoff else {}
    call_command(COMMAND_NAME, "export", file=str(file_path), **export_options)

    records = json.loads(file_path.read_text())
    expected_records = [
        {
            "bk_app_code": app_code,
            "gateway_name": gateway.name,
            "resource_name": resource.name if permission_model is AppResourcePermission else "*",
            "expires": expires.astimezone(datetime.timezone.utc).isoformat() if expires else None,
        }
        for app_code, expires in active_expirations.items()
    ]
    assert sorted(records, key=lambda record: record["bk_app_code"]) == expected_records

    # Import into objects with the original names and different IDs, leaving the source permissions intact.
    gateway.name = "original-gateway"
    gateway.display_name = "original-gateway"
    gateway.save(update_fields=["name", "display_name"])
    target_gateway = G(Gateway, name="source-gateway")
    target_resource = G(Resource, gateway=target_gateway, name=resource.name)
    assert target_gateway.id != gateway.id
    assert target_resource.id != resource.id
    call_command(COMMAND_NAME, "import", file=str(file_path))
    call_command(COMMAND_NAME, "import", file=str(file_path))

    imported = {perm.bk_app_code: perm for perm in permission_model.objects.filter(gateway=target_gateway)}
    assert set(imported) == {"permanent-app", "future-app", "sentinel-app"}
    for app_code, perm in imported.items():
        assert perm.expires == (NeverExpiresTime.time if expirations[app_code] is None else expirations[app_code])
        if permission_model is AppResourcePermission:
            assert perm.resource_id == target_resource.id
            assert perm.grant_type == GrantTypeEnum.INITIALIZE.value
    assert imported["permanent-app"].expires_in is None
    assert imported["sentinel-app"].expires_in is None
    assert imported["future-app"].expires_in > 0
    assert permission_model.objects.filter(gateway=gateway).count() == len(expirations)
    other_model = AppGatewayPermission if permission_model is AppResourcePermission else AppResourcePermission
    assert not other_model.objects.filter(gateway=target_gateway).exists()

    call_command(
        COMMAND_NAME,
        "export",
        file=str(file_path),
        ignore_gateway_names=gateway.name,
        **export_options,
    )
    restored_records = [
        {**record, "expires": NeverExpiresTime.time.isoformat() if record["expires"] is None else record["expires"]}
        for record in expected_records
    ]
    assert sorted(json.loads(file_path.read_text()), key=lambda record: record["bk_app_code"]) == restored_records
    assert permission_model.objects.get(gateway=gateway, bk_app_code="permanent-app").expires is None


@pytest.mark.parametrize("permission_model", PERMISSION_MODELS)
@pytest.mark.parametrize("expires", [None, NeverExpiresTime.time], ids=["null", "sentinel"])
def test_export_permanent_permissions_respects_ignore_lists(permission_model, expires, tmp_path):
    gateway = G(Gateway, name="included-gateway")
    ignored_gateway = G(Gateway, name="ignored-gateway")
    for permission_gateway, app_code in [
        (gateway, "included-app"),
        (gateway, "ignored-app"),
        (ignored_gateway, "included-app"),
    ]:
        resource = G(Resource, gateway=permission_gateway, name=app_code)
        permission_fields = {"resource_id": resource.id} if permission_model is AppResourcePermission else {}
        make_permission(
            permission_model, gateway=permission_gateway, bk_app_code=app_code, expires=expires, **permission_fields
        )

    file_path = tmp_path / "permissions.json"
    call_command(
        COMMAND_NAME,
        "export",
        file=str(file_path),
        ignore_bk_app_codes=" ignored-app, ",
        ignore_gateway_names=" ignored-gateway, ",
    )
    assert json.loads(file_path.read_text()) == [
        {
            "bk_app_code": "included-app",
            "gateway_name": gateway.name,
            "resource_name": "included-app" if permission_model is AppResourcePermission else "*",
            "expires": expires.isoformat() if expires else None,
        }
    ]


@pytest.mark.parametrize("invalid_resource", ["missing", "empty-name", "other-gateway"])
def test_export_null_resource_permission_skips_invalid_resource(invalid_resource, tmp_path):
    gateway = G(Gateway)
    resource = G(Resource, gateway=gateway, name="valid-resource")
    resource_id = resource.id
    if invalid_resource == "missing":
        resource.delete()
    elif invalid_resource == "empty-name":
        resource.name = ""
        resource.save(update_fields=["name"])
    else:
        resource.gateway = G(Gateway)
        resource.save(update_fields=["gateway"])
    make_permission(AppResourcePermission, gateway=gateway, resource_id=resource_id, expires=None)

    file_path = tmp_path / "permissions.json"
    errors = StringIO()
    call_command(COMMAND_NAME, "export", file=str(file_path), stderr=errors)

    assert json.loads(file_path.read_text()) == []
    expected_warning = (
        "resource.name is empty, skip" if invalid_resource == "empty-name" else "resource not found, skip"
    )
    assert expected_warning in errors.getvalue()
