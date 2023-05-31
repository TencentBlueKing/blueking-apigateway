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

import logging

from django.core.management.base import BaseCommand

from esb.bkcore.models import ComponentDoc, ESBChannel
from esb.management.utils.api_docs import ApiDocManager, DocNotChangedException

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """update api_doc to db"""

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", dest="all", default=False, help="update all api docs")

    def handle(self, *args, **options):
        self.update_api_docs(is_update_all_api_doc=options["all"])

    def update_api_docs(self, is_update_all_api_doc):
        # init api docs
        api_doc_manager = ApiDocManager(is_update_all_api_doc=is_update_all_api_doc)
        for channel in ESBChannel.objects.filter(is_active=True, is_public=True):
            try:
                api_data = api_doc_manager.get_api_doc(channel)
            except DocNotChangedException:
                continue
            except Exception:
                logger.exception("Generate apidoc fail, component_codename=%s", channel.component_codename)
                continue

            if not api_data:
                logger.warning(
                    "Oooops, No api document define found in component %s, you better write one.",
                    channel.component_codename,
                )
                continue

            for language, content in api_data["doc_md"].items():
                ComponentDoc.objects.update_or_create(
                    component=channel,
                    language=language,
                    defaults={
                        "content": content,
                        "content_md5": api_data["raw_doc_md_md5"],
                    },
                )
            logger.info("Document synced for api [%s](%s)", api_data["system_name"], api_data["component_name"])
