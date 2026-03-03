# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apigateway.apps.permission.constants import GrantTypeEnum
from apigateway.apps.permission.models import AppGatewayPermission, AppResourcePermission
from apigateway.core.models import Gateway, Resource


def _parse_ignore_list(value: str) -> set:
    if not value or not value.strip():
        return set()
    return {x.strip() for x in value.split(",") if x.strip()}


def _parse_expire_datetime(value: str | None):
    """Parse expire_datetime arg; return timezone-aware datetime. If value is None, return timezone.now()."""
    if not value or not value.strip():
        return timezone.now()
    dt = datetime.datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _parse_expires_from_record(s: str):
    """Parse expires string from JSON record. Returns timezone-aware datetime or None on failure."""
    parsed = parse_datetime(s)
    if parsed is not None:
        return parsed
    try:
        dt = datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
    except (ValueError, TypeError):
        return None


class Command(BaseCommand):
    help = """
    Export/import AppGatewayPermission and AppResourcePermission records.

    Export: Query permissions with expires > expire_datetime and write to JSON file.
            Records are filtered by ignore_bk_app_codes and ignore_gateway_names.
            File format: [{"bk_app_code": "...", "gateway_name": "...", "resource_name": "*"|"<resource.name>", "expires": "ISO8601"}]
            Note: AppResourcePermission records with empty resource.name will be skipped.

    Import: Read JSON file and upsert permissions (grant_type=initialize for AppResourcePermission).
            Skip records with missing gateway/resource and print errors.

    Examples:
        python manage.py permission_export_import export --file=perms.json
        python manage.py permission_export_import export --file=perms.json --expire-datetime="2026-01-19 11:00:00" --ignore-bk-app-codes="foo,bar" --ignore-gateway-names="bk-esb,demo"
        python manage.py permission_export_import import --file=perms.json
        python manage.py permission_export_import import --file=perms.json --ignore-gateway-names="bk-esb,demo"
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["export", "import"],
            help="export: write AppGatewayPermission and AppResourcePermission to file; import: read and upsert",
        )
        parser.add_argument(
            "--file", "-f", type=str, required=True, help="Output path for export, input path for import"
        )
        parser.add_argument(
            "--expire-datetime",
            type=str,
            default=None,
            help='For export: only include records with expires > this. Format "%%Y-%%m-%%d %%H:%%M:%%S" (e.g. 2026-01-19 11:00:00). Default: now.',
        )
        parser.add_argument(
            "--ignore-bk-app-codes",
            type=str,
            default="",
            help="Comma-separated bk_app_code to exclude (e.g. foo,bar)",
        )
        parser.add_argument(
            "--ignore-gateway-names",
            type=str,
            default="",
            help="Comma-separated gateway_name to exclude (e.g. hello,world)",
        )

    def _export(self, file_path: str, expire_datetime, ignore_bk_app_codes: set, ignore_gateway_names: set) -> None:
        records = []

        # AppGatewayPermission
        qs = AppGatewayPermission.objects.filter(expires__gt=expire_datetime).select_related("gateway")
        for perm in qs:
            if perm.bk_app_code in ignore_bk_app_codes or perm.gateway.name in ignore_gateway_names:
                continue
            records.append(
                {
                    "bk_app_code": perm.bk_app_code,
                    "gateway_name": perm.gateway.name,
                    "resource_name": "*",
                    "expires": perm.expires.isoformat() if perm.expires else None,
                }
            )

        # AppResourcePermission
        qs = AppResourcePermission.objects.filter(expires__gt=expire_datetime).select_related("gateway")
        for perm in qs:
            if perm.bk_app_code in ignore_bk_app_codes or perm.gateway.name in ignore_gateway_names:
                continue
            resource = Resource.objects.filter(gateway_id=perm.gateway_id, id=perm.resource_id).first()
            if resource is None:
                self.stderr.write(
                    f"warning: AppResourcePermission id={perm.id} resource_id={perm.resource_id} "
                    "resource not found, skip"
                )
                continue
            if not resource.name:
                self.stderr.write(
                    f"warning: AppResourcePermission id={perm.id} resource_id={perm.resource_id} "
                    "resource.name is empty, skip"
                )
                continue
            records.append(
                {
                    "bk_app_code": perm.bk_app_code,
                    "gateway_name": perm.gateway.name,
                    "resource_name": resource.name,
                    "expires": perm.expires.isoformat() if perm.expires else None,
                }
            )

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f"Exported {len(records)} records to {file_path}"))

    def _import(self, file_path: str, ignore_bk_app_codes: set, ignore_gateway_names: set) -> None:  # noqa: C901, PLR0912, PLR0915
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            self.stderr.write("error: file must contain a JSON array")
            return

        created = 0
        updated = 0
        skipped = 0

        for i, rec in enumerate(data):
            if not isinstance(rec, dict):
                self.stderr.write(f"error: record at index {i} is not an object, skip")
                skipped += 1
                continue

            bk_app_code = rec.get("bk_app_code")
            gateway_name = rec.get("gateway_name")
            resource_name = rec.get("resource_name")
            expires_str = rec.get("expires")

            if not bk_app_code or not gateway_name or resource_name is None:
                self.stderr.write(f"error: record at index {i} missing bk_app_code/gateway_name/resource_name, skip")
                skipped += 1
                continue

            if bk_app_code in ignore_bk_app_codes or gateway_name in ignore_gateway_names:
                skipped += 1
                continue

            expires = _parse_expires_from_record(expires_str) if expires_str else None
            if expires_str and expires is None:
                self.stderr.write(f"error: record at index {i} invalid expires={expires_str!r}, skip")
                skipped += 1
                continue

            if resource_name == "*":
                # AppGatewayPermission
                gateway = Gateway.objects.filter(name=gateway_name).first()
                if not gateway:
                    self.stderr.write(f"error: gateway_name={gateway_name!r} not found, skip")
                    skipped += 1
                    continue
                obj, created_flag = AppGatewayPermission.objects.update_or_create(
                    bk_app_code=bk_app_code,
                    gateway=gateway,
                    defaults={"expires": expires},
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1
            else:
                # AppResourcePermission
                gateway = Gateway.objects.filter(name=gateway_name).first()
                if not gateway:
                    self.stderr.write(f"error: gateway_name={gateway_name!r} not found, skip")
                    skipped += 1
                    continue
                resource = Resource.objects.filter(gateway=gateway, name=resource_name).first()
                if not resource:
                    self.stderr.write(
                        f"error: gateway_name={gateway_name!r} resource_name={resource_name!r} "
                        "resource not found, skip"
                    )
                    skipped += 1
                    continue
                obj, created_flag = AppResourcePermission.objects.update_or_create(
                    bk_app_code=bk_app_code,
                    gateway=gateway,
                    resource_id=resource.id,
                    defaults={"expires": expires, "grant_type": GrantTypeEnum.INITIALIZE.value},
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Import done: created={created}, updated={updated}, skipped={skipped}"))

    def handle(self, action, file, expire_datetime, ignore_bk_app_codes, ignore_gateway_names, **options):
        ignore_bk = _parse_ignore_list(ignore_bk_app_codes or "")
        ignore_gw = _parse_ignore_list(ignore_gateway_names or "")

        if action == "export":
            exp_dt = _parse_expire_datetime(expire_datetime)
            self._export(file, exp_dt, ignore_bk, ignore_gw)
        else:
            self._import(file, ignore_bk, ignore_gw)
