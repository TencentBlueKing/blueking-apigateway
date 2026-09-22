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

APPLY_STATUS_CHOICES = [
    ("partial_approved", "部分通过"),
    ("approved", "全部通过"),
    ("rejected", "全部驳回"),
    ("pending", "待审批"),
    ("canceled", "已取消"),
]


class Migration(migrations.Migration):
    dependencies = [
        ("permission", "0013_add_permission_handled_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="apppermissionapply",
            name="status",
            field=models.CharField(choices=APPLY_STATUS_CHOICES, db_index=True, max_length=16),
        ),
        migrations.AlterField(
            model_name="apppermissionapplystatus",
            name="status",
            field=models.CharField(choices=APPLY_STATUS_CHOICES, max_length=16),
        ),
        migrations.AlterField(
            model_name="apppermissionrecord",
            name="status",
            field=models.CharField(choices=APPLY_STATUS_CHOICES, db_index=True, max_length=16),
        ),
    ]
