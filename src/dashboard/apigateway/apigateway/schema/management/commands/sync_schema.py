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
from django.core.management.base import BaseCommand
from django.utils import timezone

from apigateway.schema.data import meta_schema
from apigateway.schema.models import Schema


class Command(BaseCommand):
    def handle(self, *args, **options):
        meta_schemas = meta_schema.init_meta_schemas()
        for s in meta_schemas:
            obj, created = Schema.objects.update_or_create(
                name=s.name,
                type=s.type,
                version=s.version,
                defaults={
                    "schema": s.schema,
                    "description": s.description,
                    "example": s.example,
                },
            )

            if created:
                obj.created_time = timezone.now()
            obj.updated_time = timezone.now()
            obj.save()

        print("Done")
