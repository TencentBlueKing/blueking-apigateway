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
from django.db.models import Count

from apigateway.apps.plugin.models import PluginBinding


class Command(BaseCommand):
    """检查插件绑定与插件配置绑定关系是否从多对多迁移到一对多"""

    def handle(self, *args, **options):
        if PluginBinding.objects.values("config_id").annotate(cnt=Count("config_id")).filter(cnt__gte=2).count() > 0:
            raise Exception("插件绑定与插件配置绑定关系存在多对多关系, 请检查迁移是否正确")  # noqa

        self.stdout.write("check migrate plugin binding ok, no problem")
