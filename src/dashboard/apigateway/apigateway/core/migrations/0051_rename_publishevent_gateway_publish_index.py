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
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0050_publishevent_created_time_idx"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RenameIndex(
                    model_name="publishevent",
                    new_name="core_publis_gateway_581387_idx",
                    old_fields=("gateway_id", "publish_id"),
                ),
            ],
            state_operations=[
                migrations.AlterIndexTogether(
                    name="publishevent",
                    index_together=set(),
                ),
                migrations.AddIndex(
                    model_name="publishevent",
                    index=models.Index(
                        fields=["gateway", "publish"],
                        name="core_publis_gateway_581387_idx",
                    ),
                ),
            ],
        ),
    ]
