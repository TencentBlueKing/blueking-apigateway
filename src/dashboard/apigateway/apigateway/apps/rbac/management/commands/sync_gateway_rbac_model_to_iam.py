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
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apigateway.biz.iam import GatewayIAMModelSyncer


class Command(BaseCommand):
    help = "将网关 RBAC 模型同步到权限中心 V4"

    def handle(self, *args, **options):
        if not settings.BK_IAM_V4_ENABLED:
            self.stdout.write("BK_IAM_V4_ENABLED=false; skipped")
            return

        self._validate_settings()
        try:
            result = GatewayIAMModelSyncer().sync()
        except Exception as err:
            raise CommandError(f"同步网关 RBAC 模型到权限中心失败: {err}") from err

        self.stdout.write(
            "created={created} updated={updated} unchanged={unchanged} "
            "action-bindings-added={added} action-bindings-deleted={deleted} "
            "action-bindings-unchanged={bindings_unchanged}".format(
                created=result.created,
                updated=result.updated,
                unchanged=result.unchanged,
                added=result.action_bindings_added,
                deleted=result.action_bindings_deleted,
                bindings_unchanged=result.action_bindings_unchanged,
            )
        )

    def _validate_settings(self) -> None:
        parsed_url = urlparse(settings.BK_IAM_V4_API_URL)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise CommandError("BK_IAM_V4_API_URL 必须是有效的 HTTP(S) URL")

        managers = settings.BK_IAM_V4_MANAGERS
        if not managers or any(not isinstance(manager, str) or not manager.strip() for manager in managers):
            raise CommandError("BK_IAM_V4_MANAGERS 必须至少配置一个非空管理员")
