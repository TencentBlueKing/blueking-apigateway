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
# Generated by Django 2.0.13 on 2019-11-27 02:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="APILabel",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_time", models.DateTimeField(blank=True, null=True)),
                ("updated_time", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.CharField(blank=True, max_length=32, null=True)),
                ("updated_by", models.CharField(blank=True, max_length=32, null=True)),
                ("name", models.CharField(max_length=32)),
                ("api", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.API")),
            ],
            options={
                "verbose_name": "API标签集",
                "verbose_name_plural": "API标签集",
                "db_table": "label_api",
            },
        ),
        migrations.CreateModel(
            name="ResourceLabel",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_time", models.DateTimeField(blank=True, null=True)),
                ("updated_time", models.DateTimeField(blank=True, null=True)),
                ("api_label", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="label.APILabel")),
                ("resource", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.Resource")),
            ],
            options={
                "verbose_name": "Resource标签",
                "verbose_name_plural": "Resource标签",
                "db_table": "label_resource",
            },
        ),
        migrations.AlterUniqueTogether(
            name="resourcelabel",
            unique_together={("resource", "api_label")},
        ),
        migrations.AlterUniqueTogether(
            name="apilabel",
            unique_together={("api", "name")},
        ),
    ]
