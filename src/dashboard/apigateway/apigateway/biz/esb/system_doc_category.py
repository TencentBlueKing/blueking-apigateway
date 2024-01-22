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

from django.conf import settings

from apigateway.apps.esb.bkcore.models import ComponentSystem, ESBChannel
from apigateway.biz.esb.board_config import BoardConfigManager
from apigateway.common.i18n.field import SerializerTranslatedField


class SystemDocCategoryHandler:
    @classmethod
    def get_system_doc_categories(cls):
        if getattr(settings, "SYSTEM_DOC_CATEGORIES", None):
            return cls._get_system_doc_categories_by_settings()

        return cls._get_system_doc_categories_by_db()

    @staticmethod
    def _get_system_doc_categories_by_db():
        from apigateway.apps.esb.bkcore.models import DocCategory, SystemDocCategory
        from apigateway.apps.esb.constants import DataTypeEnum

        board_to_category_ids = SystemDocCategory.objects.group_category_id_by_board()
        category_id_to_system_ids = SystemDocCategory.objects.group_system_id_by_category_id()
        category_id_to_fields_map = DocCategory.objects.get_id_to_fields_map()
        system_id_to_fields_map = ComponentSystem.objects.get_id_to_fields_map()

        # 包含公开组件，且非官方隐藏的系统
        official_hidden_system_ids = ComponentSystem.objects.filter(
            data_type=DataTypeEnum.OFFICIAL_HIDDEN.value
        ).values_list("id", flat=True)
        system_ids = ESBChannel.objects.filter_active_and_public_system_ids()
        system_ids = set(system_ids) - set(official_hidden_system_ids)

        name_field = SerializerTranslatedField(
            translated_fields={"en": "name_en"},
            default_field="name",
            allow_blank=True,
        )
        description_field = SerializerTranslatedField(
            translated_fields={"en": "description_en"},
            default_field="description",
            allow_blank=True,
        )

        category_systems = []
        for board, category_ids in board_to_category_ids.items():
            category = {
                "board": board,
                "board_label": BoardConfigManager.get_board_label(board),
                "categories": [],
            }

            sorted_category_ids = sorted(
                category_ids,
                key=lambda x: category_id_to_fields_map[x]["priority"],
                reverse=True,
            )

            for category_id in sorted_category_ids:
                systems = [
                    {
                        "name": system_id_to_fields_map[system_id]["name"],
                        "description": description_field.get_attribute(system_id_to_fields_map[system_id]),
                    }
                    for system_id in category_id_to_system_ids[category_id]
                    if system_id in system_ids
                ]
                if not systems:
                    continue

                category["categories"].append(
                    {
                        "id": category_id,
                        "name": name_field.get_attribute(category_id_to_fields_map[category_id]),
                        "systems": systems,
                    }
                )

            category_systems.append(category)

        return category_systems

    @staticmethod
    def _get_system_doc_categories_by_settings():
        system_categories = copy.deepcopy(settings.SYSTEM_DOC_CATEGORIES)
        for category in system_categories:
            board_config = BoardConfigManager.get_board_config(category["board"])
            category["board_label"] = board_config.label
        return system_categories
