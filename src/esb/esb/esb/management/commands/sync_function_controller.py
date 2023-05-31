# -*- coding: utf-8 -*-
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

import re

from django.core.management.base import BaseCommand

from esb.bkcore.models import FunctionController
from esb.management.utils.constants import FUNCTION_CONTROLLERS


class Command(BaseCommand):
    """将系统和通道Channel数据，更新到数据库中"""

    def handle(self, *args, **options):
        update_function_controller()


def update_function_controller():
    delimiter = re.compile(r"[^,;]+")
    for func_ctl in FUNCTION_CONTROLLERS:
        func_code = func_ctl.pop("func_code")
        obj, created = FunctionController.objects.get_or_create(func_code=func_code, defaults=func_ctl)
        if not created:
            new_wlist = delimiter.findall(func_ctl["wlist"])
            now_wlist = delimiter.findall(obj.wlist)
            wlist = set()
            wlist.update(new_wlist)
            wlist.update(now_wlist)
            obj.wlist = ",".join(sorted(list(wlist)))
            obj.save()
