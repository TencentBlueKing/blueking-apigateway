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
import json
import logging

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from apigateway.apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apigateway.common.plugin.header_rewrite import HeaderRewriteConvertor
from apigateway.apigateway.core.constants import ContextScopeTypeEnum, ContextTypeEnum
from apigateway.core.models import Context, Release, Stage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """将stage/resource的proxy请求头配置迁移成bk-header-rewrite插件配置"""

    def handle(self, *args, **options):
        # 遍历stage, 迁移proxy请求头
        qs = Stage.objects.prefetch_related("api").all()

        logger.info("start migrate header rewrite plugin config, all stage count %s", qs.count())

        paginator = Paginator(qs, 100)
        for i in paginator.page_range:

            logger.info("migrate stage count %s", (i + 1) * 100)

            for stage in paginator.page(i):
                context = Context.objects.filter(
                    scope_type=ContextScopeTypeEnum.STAGE.value,
                    scope_id=stage.id,
                    type=ContextTypeEnum.STAGE_PROXY_HTTP.value,
                ).first()

                # 1. 迁移stage的proxy请求头
                stage_transform_headers = context.config.get("transform_headers", {}) if context else {}
                stage_config = HeaderRewriteConvertor.transform_headers_to_plugin_config(stage_transform_headers)
                HeaderRewriteConvertor.alter_plugin(
                    stage.api, PluginBindingScopeEnum.STAGE.value, stage.id, stage_config
                )

                # 2. 迁移resource的proxy请求头
                release = Release.objects.filter(stage=stage).prefetch_related("resource_version").first()
                if not release:
                    continue

                for resource in release.resource_version.data:
                    resource_proxy = json.loads(resource["proxy"]["config"])
                    resource_transform_headers = resource_proxy.get("transform_headers", {})
                    resource_config = HeaderRewriteConvertor.transform_headers_to_plugin_config(
                        resource_transform_headers
                    )

                    plugin_config = HeaderRewriteConvertor.merge_plugin_config(stage_config, resource_config)
                    HeaderRewriteConvertor.alter_plugin(
                        stage.api, PluginBindingScopeEnum.RESOURCE.value, resource["id"], plugin_config
                    )

        logger.info("finish migrate header rewrite plugin config")
