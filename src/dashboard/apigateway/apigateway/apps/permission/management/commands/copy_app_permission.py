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
from django.core.management.base import BaseCommand

from apigateway.apps.permission.models import AppGatewayPermission, AppResourcePermission


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--src-app", type=str, dest="src_app", required=True)
        parser.add_argument("--dst-app", type=str, dest="dst_app", required=True)
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="dry run")

    def _copy_api_permission(self, src_app, dst_app):
        for src_perm in AppGatewayPermission.objects.filter(bk_app_code=src_app):
            dst_perm, created = AppGatewayPermission.objects.get_or_create(
                bk_app_code=dst_app,
                gateway_id=src_perm.gateway_id,
                defaults={
                    "expires": src_perm.expires,
                },
            )
            if not created and src_perm.expires > dst_perm.expires:
                dst_perm.expires = src_perm.expires
                dst_perm.save(update_fields=["expires"])

    def _copy_resource_permission(self, src_app, dst_app):
        for src_perm in AppResourcePermission.objects.filter(bk_app_code=src_app):
            dst_perm, created = AppResourcePermission.objects.get_or_create(
                bk_app_code=dst_app,
                gateway_id=src_perm.gateway_id,
                resource_id=src_perm.resource_id,
                defaults={
                    "expires": src_perm.expires,
                    "grant_type": src_perm.grant_type,
                },
            )
            if not created and src_perm.expires > dst_perm.expires:
                dst_perm.expires = src_perm.expires
                dst_perm.save(update_fields=["expires"])

    def _copy_api_permission_dry_run(self, src_app, dst_app):
        for src_perm in AppGatewayPermission.objects.filter(bk_app_code=src_app):
            try:
                dst_perm = AppGatewayPermission.objects.get(bk_app_code=dst_app, gateway_id=src_perm.gateway_id)
            except AppGatewayPermission.DoesNotExist:
                print(
                    f"add new perm: bk_app_code={dst_app}, gateway_id={src_perm.gateway_id}, expires={src_perm.expires}"
                )
            else:
                if dst_perm.expires < src_perm.expires:
                    print(
                        f"update perm expires: bk_app_code={dst_app}, gateway_id={src_perm.gateway_id}, "
                        f"expires={src_perm.expires}"
                    )
                else:
                    print(
                        f"perm exist and ignore: bk_app_code={dst_app}, gateway_id={src_perm.gateway_id}, "
                        f"expires={dst_perm.expires}"
                    )

    def _copy_resource_permission_dry_run(self, src_app, dst_app):
        for src_perm in AppResourcePermission.objects.filter(bk_app_code=src_app):
            try:
                dst_perm = AppResourcePermission.objects.get(
                    bk_app_code=dst_app,
                    gateway_id=src_perm.gateway_id,
                    resource_id=src_perm.resource_id,
                )
            except AppResourcePermission.DoesNotExist:
                print(
                    f"add new perm: bk_app_code={dst_app}, gateway_id={src_perm.gateway_id}, "
                    f"resource_id={src_perm.resource_id}, expires={src_perm.expires}"
                )
            else:
                if dst_perm.expires < src_perm.expires:
                    print(
                        f"update perm expires: bk_app_code={dst_app}, gateway_id={src_perm.gateway_id}, "
                        f"resource_id={src_perm.resource_id}, expires={src_perm.expires}"
                    )
                else:
                    print(
                        f"perm exist and ignore: bk_app_code={dst_app}, gateway_id={src_perm.gateway_id}, "
                        f"resource_id={src_perm.resource_id}, expires={dst_perm.expires}"
                    )

    def handle(self, src_app, dst_app, dry_run, **options):
        if dry_run:
            print(f"copy app[{src_app}] permission to app[{dst_app}]")
            self._copy_api_permission_dry_run(src_app, dst_app)
            self._copy_resource_permission_dry_run(src_app, dst_app)
            return

        self._copy_api_permission(src_app, dst_app)
        self._copy_resource_permission(src_app, dst_app)
