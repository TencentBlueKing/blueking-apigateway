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
import copy
import itertools
import logging
import operator

from django.core.management.base import BaseCommand
from django.db import transaction

from apigateway.apps.esb.bkcore.models import AppComponentPermission, ESBChannel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)

    @transaction.atomic
    def handle(self, dry_run: bool, *args, **options):
        self._split_component_method(dry_run)

    def _split_component_method(self, dry_run: bool):  # noqa
        components = list(ESBChannel.objects.values("id", "method", "path"))

        components = sorted(components, key=operator.itemgetter("path"))
        for path, group in itertools.groupby(components, key=operator.itemgetter("path")):
            method_to_component = {component["method"]: component for component in group}
            if len(method_to_component) == 1:
                continue

            # method = "" 为 GET/POST 方法
            if "" not in method_to_component:
                continue

            empty_method_component_id = method_to_component[""]["id"]
            empty_method_component = ESBChannel.objects.get(id=empty_method_component_id)
            current_methods = list(method_to_component.keys())
            if "GET" in method_to_component and "POST" in method_to_component:
                # method=GET、POST 均已存在，method="" 实际未使用，请求确认删除
                if dry_run:
                    logger.warning(
                        f"组件路径 [{path}] 下，存在请求方法：{current_methods}，"
                        f"其中请求方法为 '' [id={empty_method_component_id}] 的组件实际未使用，将删除该组件"
                    )
                    continue

                confirm = input(
                    f"组件路径 [{path}] 下，存在请求方法：{current_methods}，"
                    f"其中请求方法为 '' [id={empty_method_component_id}] 的组件实际未使用，请确认是否删除：yes/no?"
                )
                if confirm == "yes":
                    empty_method_component.delete()

            elif "GET" in method_to_component and "POST" not in method_to_component:
                # method GET 存在，POST 不存在，则将 "" 改为 POST
                if not dry_run:
                    empty_method_component.method = "POST"
                    empty_method_component.save(update_fields=["method"])
                logger.info(
                    f"组件路径 [{path}] 下，存在请求方法：['', 'GET']，将组件 [id={empty_method_component_id}] 的请求方法由 '' 改为 POST"
                )

            elif "GET" not in method_to_component and "POST" in method_to_component:
                # method GET 不存在，POST 存在，则将 "" 改为 GET
                if not dry_run:
                    empty_method_component.method = "GET"
                    empty_method_component.save(update_fields=["method"])
                logger.info(
                    f"组件路径 [{path}] 下，存在请求方法：['',  POST]，将组件 [id={empty_method_component_id}] 的请求方法由 '' 改为 GET"
                )

            elif "GET" not in method_to_component and "POST" not in method_to_component:
                # GET、POST 均不存在，则将 "" 改为 suggest_method，并新建另一个 method 的组件
                if dry_run:
                    logger.warning(
                        f"组件路径 [{path}] 下，存在请求方法：{current_methods}，"
                        f"需将请求方法为 '' 的组件 [id={empty_method_component_id}] 拆分为请求方法分别为 GET、POST 的两个组件"
                    )
                    continue

                suggest_method = empty_method_component.config.get("suggest_method")
                if suggest_method in ["GET", "POST"]:
                    confirm = input(
                        f"组件路径 [{path}] 下，存在请求方法：{current_methods}，"
                        f"需将请求方法为 '' 的组件 [id={empty_method_component_id}] 拆分为请求方法分别为 GET、POST 的两个组件，"
                        f"因组件 suggest_method 为 {suggest_method}，因此将当前组件请求访问改为 {suggest_method}，同时新建另一个请求方法的组件，"
                        f"请确认：yes/no?"
                    )
                    if confirm == "yes":
                        empty_method_component.method = suggest_method
                        empty_method_component.save(update_fields=["method"])
                        another_component = self._create_component_with_another_method(empty_method_component)
                        self._copy_component_permission(empty_method_component.id, another_component.id)

                else:
                    confirm = input(
                        f"组件路径 [{path}] 下，存在请求方法：{current_methods}，"
                        f"需将请求方法为 '' 的组件 [id={empty_method_component_id}] 拆分为请求方法分别为 GET、POST 的两个组件，"
                        f"请确认：yes/no?"
                    )
                    if confirm == "yes":
                        confirm = input("请输入推荐的请求方法：GET or POST?")
                        suggest_method = confirm.upper()
                        if suggest_method in ["GET", "POST"]:
                            empty_method_component.method = suggest_method
                            empty_method_component.save(update_fields=["method"])
                            another_component = self._create_component_with_another_method(empty_method_component)
                            self._copy_component_permission(empty_method_component.id, another_component.id)

    def _create_component_with_another_method(self, src_component: ESBChannel) -> ESBChannel:
        dst_component = copy.deepcopy(src_component)
        dst_component.id = None
        dst_component.method = "POST" if src_component.method == "GET" else "GET"
        dst_component.is_public = False
        # 防止组件名称重复，为拆分出去的组件的组件名，添加后缀
        dst_component.name = f"{src_component.name}__split"
        dst_component.save()

        assert dst_component.id

        return dst_component

    def _copy_component_permission(self, src_component_id: int, dst_component_id: int):
        for src_permission in AppComponentPermission.objects.filter(component_id=src_component_id):
            AppComponentPermission.objects.get_or_create(
                bk_app_code=src_permission.bk_app_code,
                component_id=dst_component_id,
                defaults={
                    "expires": src_permission.expires,
                },
            )
