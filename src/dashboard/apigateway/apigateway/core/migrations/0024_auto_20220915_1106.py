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
# Generated by Django 2.0.13 on 2022-09-15 03:06

import uuid

import django.db.models.deletion
import jsonfield.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_auto_20220422_1534"),
    ]

    operations = [
        migrations.AddField(
            model_name="microgateway",
            name="is_managed",
            field=models.BooleanField(default=True, help_text="是否托管实例"),
        ),
        migrations.AlterField(
            model_name="backendservice",
            name="description",
            field=models.TextField(blank=True, default="", null=True),
        ),
        migrations.AlterField(
            model_name="context",
            name="type",
            field=models.CharField(
                choices=[
                    ("api_auth", "API_AUTH"),
                    ("resource_auth", "RESOURCE_AUTH"),
                    ("stage_proxy_http", "STAGE_PROXY_HTTP"),
                    ("stage_rate_limit", "STAGE_RATE_LIMIT"),
                    ("api_feature_flag", "API_FEATURE_FLAG"),
                ],
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="microgateway",
            name="id",
            field=models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="microgateway",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "待安装"),
                    ("installing", "安装中"),
                    ("installed", "已安装"),
                    ("updated", "已更新"),
                    ("abnormal", "安装异常"),
                ],
                default="pending",
                max_length=64,
            ),
        ),
        migrations.AlterField(
            model_name="microgatewayreleasehistory",
            name="details",
            field=jsonfield.fields.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="releasehistory",
            name="message",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="resourceversion",
            name="comment",
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name="resourceversion",
            name="title",
            field=models.CharField(blank=True, default="", max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name="stage",
            name="micro_gateway",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="core.MicroGateway",
            ),
        ),
    ]
