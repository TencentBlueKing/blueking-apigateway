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
# Generated by Django 3.2.18 on 2023-08-15 02:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plugin", "0008_auto_20230815_1005"),
    ]

    operations = [
        migrations.AlterField(
            model_name="plugin",
            name="type",
            field=models.CharField(
                choices=[
                    ("ip-restriction", "IP访问控制"),
                    ("rate_limit", "频率控制"),
                    ("cors", "CORS"),
                    ("bk-verified-user-exempted-apps", "免用户认证应用白名单"),
                ],
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="pluginbinding",
            name="type",
            field=models.CharField(
                choices=[
                    ("ip-restriction", "IP访问控制"),
                    ("rate_limit", "频率控制"),
                    ("cors", "CORS"),
                    ("bk-verified-user-exempted-apps", "免用户认证应用白名单"),
                ],
                max_length=32,
                null=True,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="pluginbinding",
            unique_together={("scope_id", "scope_type", "config")},
        ),
    ]
