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

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("permission", "0011_add_itsm_ticket_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="appapipermission",
            name="grant_type",
            field=models.CharField(
                choices=[
                    ("initialize", "主动授权"),
                    ("apply", "申请审批"),
                    ("renew", "续期"),
                    ("auto_renew", "自动续期"),
                    ("sync", "按网关授权同步"),
                ],
                db_index=True,
                default="initialize",
                max_length=16,
            ),
        ),
    ]
