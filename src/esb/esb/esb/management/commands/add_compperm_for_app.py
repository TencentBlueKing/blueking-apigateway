# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
from django.core.management.base import BaseCommand, CommandError

from esb.bkcore.models import AppComponentPermission, ESBChannel


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--app_code", action="store", dest="app_code")
        parser.add_argument("--system_name", action="store", dest="system_name")
        parser.add_argument("--component_name", action="store", dest="component_name")

    def handle(self, *args, **options):
        app_code = options["app_code"]
        system_name = options["system_name"]
        component_name = options["component_name"]

        if not app_code:
            raise CommandError("应用编码 app_code 不能为空")

        components = ESBChannel.objects.all()
        if system_name:
            components = components.filter(system__name=system_name)
        if component_name:
            components = components.filter(name__in=component_name.split(","))
        components = components.values("id", "name", "system__name")

        for component in components:
            obj, created = AppComponentPermission.objects.get_or_create(
                bk_app_code=app_code,
                component_id=component["id"],
            )

            system_name = component["system__name"]
            component_name = component["name"]
            tip = "add perm" if created else "has perm, ignore"
            tip = f"{tip}: bk_app_code={app_code}, system_name={system_name}, component_name={component_name}"
            print(tip)

        print("Done, count: {count}".format(count=len(components)))
