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
from __future__ import print_function

import json

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """检测服务可用性"""

    def add_arguments(self, parser):
        parser.add_argument("--service", action="store", dest="service", help="Service name")

    def handle(self, *args, **options):
        self.check_job_ssl()

    def check_job_ssl(self):
        from components.bk.apis.job.get_agent_status import GetAgentStatus

        kwargs = {
            "app_id": 1,
            "ip_infos": [
                {
                    "ip": "127.0.0.1",
                    "plat_id": 1,
                }
            ],
        }
        result = GetAgentStatus().invoke(kwargs=kwargs)
        print("check_job_ssl:", json.dumps(result))
        assert result["result"], result["message"]
