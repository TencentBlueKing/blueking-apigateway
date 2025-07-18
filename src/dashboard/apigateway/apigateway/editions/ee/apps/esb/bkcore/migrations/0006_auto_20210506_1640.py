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
# Generated by Django 2.0.13 on 2021-05-06 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bkcore", "0005_auto_20210425_1602"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessToken",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_time", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_time", models.DateTimeField(auto_now=True, null=True)),
                ("bk_app_code", models.CharField(max_length=128, verbose_name="蓝鲸智云应用编码")),
                ("user_id", models.CharField(max_length=64, verbose_name="用户标识")),
                ("access_token", models.CharField(max_length=255, verbose_name="token内容")),
                ("expires", models.DateTimeField(verbose_name="token过期时间")),
            ],
            options={
                "db_table": "esb_access_token",
            },
        ),
        migrations.AlterUniqueTogether(
            name="accesstoken",
            unique_together={("bk_app_code", "user_id")},
        ),
    ]
