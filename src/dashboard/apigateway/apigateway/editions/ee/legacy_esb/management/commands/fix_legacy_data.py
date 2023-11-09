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
"""修复 PaaS2/ESB 中的部分数据"""
import logging
from typing import List

from django.core.management.base import BaseCommand

from apigateway.legacy_esb import models as legacy_models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self._fix_legacy_doc_category()

    def _fix_legacy_doc_category(self):
        duplicate_names = legacy_models.SystemDocCategory.objects.get_duplicate_names()
        if not duplicate_names:
            return

        if self._is_confirmed_fix_legacy_doc_category(duplicate_names):
            legacy_models.SystemDocCategory.objects.delete_duplicate_names()

    def _is_confirmed_fix_legacy_doc_category(self, duplicate_names: List[str]) -> bool:
        confirm = input(
            f"旧版文档分类 `name={', '.join(duplicate_names)}` 重复，请确认是否更新组件系统所属的文档分类，并删除重复的文档分类：yes/no?"
        )
        return confirm == "yes"
