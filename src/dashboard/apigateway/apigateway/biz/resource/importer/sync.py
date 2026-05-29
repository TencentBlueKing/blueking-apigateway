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
import json
import logging
from typing import Tuple

from django.utils.html import escape as html_escape

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.openapi import OpenAPIImportManager
from apigateway.biz.resource_doc.importer import DocImporter, OpenAPIParser
from apigateway.core.models import Gateway

from .importers import ResourcesImporter

logger = logging.getLogger(__name__)


def sync_openapi_resources_from_content(
    gateway: Gateway,
    username: str,
    content: str,
    delete_missing_resources: bool,
    doc_language: str = "",
) -> Tuple[bool, str, dict]:
    """
    Sync OpenAPI resources from content.

    Returns:
        Tuple[bool, str, dict]: (ok, message, data)
            - ok: True if sync succeeded, False otherwise
            - message: Error message if failed, empty string if succeeded
            - data: Dict with keys "added", "updated", "deleted" if succeeded, empty dict if failed
    """
    try:
        openapi_manager = OpenAPIImportManager.load_from_content(
            gateway,
            content,
            need_delete_unspecified_resources=delete_missing_resources,
        )
    except Exception as err:
        logger.exception("failed to load openapi content")
        return (
            False,
            f"导入内容为无效的 json/yaml 数据，{html_escape(str(err))}。",
            {},
        )

    validate_err_list = openapi_manager.validate()
    if validate_err_list:
        error_dicts = [error.to_dict() for error in validate_err_list]
        return (
            False,
            json.dumps(error_dicts, ensure_ascii=False, indent=4),
            {},
        )

    importer = ResourcesImporter.from_resources(
        gateway=gateway,
        resources=openapi_manager.get_resource_list(),
        username=username,
        selected_resources=None,
        need_delete_unspecified_resources=delete_missing_resources,
    )
    importer.import_resources()

    if doc_language:
        parser = OpenAPIParser(gateway_id=gateway.id)
        docs: list = parser.parse(swagger=content, language=DocLanguageEnum(doc_language))
        DocImporter(gateway_id=gateway.id).import_docs(docs=docs)

    added = []
    updated = []
    for resource_data in importer.get_selected_resource_data_list():
        if resource_data.metadata.get("is_created"):
            added.append({"id": resource_data.resource.id})
        else:
            updated.append({"id": resource_data.resource.id})

    return (
        True,
        "",
        {
            "added": added,
            "updated": updated,
            "deleted": importer.get_deleted_resources(),
        },
    )
