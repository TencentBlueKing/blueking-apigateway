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
# Generated by Django 3.2.18 on 2023-10-23 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0037_auto_20230902_1307'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='APIRelatedApp',
            new_name='GatewayRelatedApp',
        ),
        migrations.AlterModelOptions(
            name='gateway',
            options={'verbose_name': 'Gateway', 'verbose_name_plural': 'Gateway'},
        ),
        migrations.AlterField(
            model_name='gateway',
            name='hosting_type',
            field=models.IntegerField(choices=[(0, 'apigateway-ng'), (1, '微网关')], default=1),
        ),
        migrations.AlterField(
            model_name='microgatewayreleasehistory',
            name='status',
            field=models.CharField(choices=[('success', 'Success'), ('failure', 'Failure'), ('pending', 'Pending'), ('releasing', 'Releasing'), ('unreleased', 'Unreleased')], default='pending', max_length=16, verbose_name='发布状态'),
        ),
        migrations.AlterField(
            model_name='releasehistory',
            name='status',
            field=models.CharField(choices=[('success', 'Success'), ('failure', 'Failure'), ('pending', 'Pending'), ('releasing', 'Releasing'), ('unreleased', 'Unreleased')], default='pending', max_length=16, verbose_name='发布状态'),
        ),
        migrations.AlterField(
            model_name='resourceversion',
            name='name',
            field=models.CharField(max_length=128, verbose_name='[Deprecated] 版本名'),
        ),
    ]