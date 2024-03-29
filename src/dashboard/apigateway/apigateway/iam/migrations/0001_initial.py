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
# Generated by Django 3.2.18 on 2023-06-28 10:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0028_auto_20230227_2006'),
    ]

    operations = [
        migrations.CreateModel(
            name='IAMUserGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_time', models.DateTimeField(auto_now=True, null=True)),
                ('role', models.CharField(default='developer', max_length=32)),
                ('user_group_id', models.IntegerField(help_text='IAM 用户组 ID')),
                ('gateway', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.gateway')),
            ],
            options={
                'verbose_name': 'IAM 用户组',
                'verbose_name_plural': 'IAM 用户组',
                'db_table': 'iam_user_group',
                'unique_together': {('gateway', 'role')},
            },
        ),
        migrations.CreateModel(
            name='IAMGradeManager',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_time', models.DateTimeField(auto_now=True, null=True)),
                ('grade_manager_id', models.IntegerField(help_text='IAM 分级管理员 ID')),
                ('gateway', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.gateway')),
            ],
            options={
                'verbose_name': 'IAM 分级管理员',
                'verbose_name_plural': 'IAM 分级管理员',
                'db_table': 'iam_grade_manager',
                'unique_together': {('gateway', 'grade_manager_id')},
            },
        ),
    ]
