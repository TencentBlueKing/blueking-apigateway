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
import json
import logging
from django.conf import settings

from django.core.management.base import BaseCommand

from common.base_utils import get_not_empty_value
from esb.bkcore.constants import DataTypeEnum, PermissionLevelEnum
from esb.bkcore.models import DocCategory, ESBChannel, ESBChannelExtend, System, SystemDocCategory
from esb.management.utils import conf_tools

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """update system and channel data to db"""

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", dest="force", help="Force data update to db")

    def handle(self, *args, **options):
        self.force = options["force"]

        self.update_doc_category()
        self.update_systems()
        self.update_channels()
        self.update_system_doc_category()

        logger.info("Sync system/channels done")

    def update_systems(self):
        default_update_fields = ["description", "comment", "description_en", "comment_en"]
        force_update_fields = []

        conf_client = conf_tools.ConfClient()
        for system_config in self._convert_system_legacy_fields_to_new(conf_client.systems):
            system, created = System.objects.get_or_create(
                name=system_config["name"],
                defaults=self.get_by_fields(system_config, default_update_fields + force_update_fields),
            )

            system.data_type = self._convert_to_data_type(system_config["is_public"])
            system.save(update_fields=["data_type"])

            if created:
                logger.info("add system: %s", system_config["name"])
                continue

            self.diff_obj_conf(
                system,
                system_config,
                "system %s" % system_config["name"],
                default_update_fields,
                force_update_fields,
            )

            system.__dict__.update(self.get_by_fields(system_config, default_update_fields))
            if self.force:
                system.__dict__.update(self.get_by_fields(system_config, force_update_fields))
            system.save()

    def update_channel_by_config(
        self, channel, config, default_update_fields, force_update_fields, allow_custom_config=False
    ):
        self.diff_obj_conf(
            channel,
            config,
            "channel %s" % config["path"],
            default_update_fields,
            force_update_fields,
        )

        channel.method = config["method"]
        channel.data_type = self._convert_to_data_type(config.get("is_public", True))

        # 如果允许用户自定义组件配置，则以用户配置为准
        if allow_custom_config:
            channel.config = self._merge_dicts(channel.config, config["force_config"])
        else:
            channel.config = self._merge_dicts(config["config"], config["force_config"])

        channel.__dict__.update(self.get_by_fields(config, default_update_fields))
        if self.force:
            channel.__dict__.update(self.get_by_fields(config, force_update_fields))

        try:
            channel.save()
        except Exception:
            logger.exception("update channel fail: channel_id=%d, config=%s", channel.pk, json.dumps(config))

        return channel

    def create_channel_by_config(self, config, default_update_fields, force_update_fields):
        esb_channel = ESBChannel(**self.get_by_fields(config, default_update_fields + force_update_fields))
        esb_channel.method = config["method"]
        esb_channel.path = config["path"]
        esb_channel.permission_level = config["permission_level"]
        esb_channel.verified_user_required = config["verified_user_required"]
        esb_channel.config = self._merge_dicts(config["config"], config["force_config"])
        esb_channel.data_type = self._convert_to_data_type(config.get("is_public", True))

        try:
            esb_channel.save()
        except Exception:
            logger.exception("create channel fail: config=%s", json.dumps(config))
            return None
        else:
            logger.info("create channel: %s %s", config["method"], config["path"])

        return esb_channel

    def update_channels(self):
        default_update_fields = ["name", "description", "method", "component_codename", "is_public", "description_en"]
        force_update_fields = ["system_id"]

        remaining_official_channel_ids = self._get_official_channel_ids()
        remaining_official_channels = dict.fromkeys(remaining_official_channel_ids, None)

        conf_client = conf_tools.ConfClient()
        for system_name, channels in list(conf_client.channels.items()):
            try:
                system = System.objects.get(name=system_name)
            except System.DoesNotExist:
                system = System.objects.create(
                    name=system_name,
                    description=system_name,
                    data_type=DataTypeEnum.OFFICIAL_PUBLIC.value,
                )

            for channel in channels:
                # 最大长度 128 个字符
                description_en = channel.get("label_en")
                if description_en:
                    description_en = description_en[:128]

                new_channel = {
                    "system_id": system.id,
                    "name": channel.get("component_name", ""),
                    "description": channel["component_label"],
                    "description_en": description_en,
                    "method": channel.get("method", ""),
                    "path": channel["path"],
                    "component_codename": channel["comp_codename"],
                    "config": channel.get("comp_conf_to_db") or {},
                    # force_config 以项目内配置为准，每次更新，与 config 合并后，强制更新至 DB
                    "force_config": get_not_empty_value(
                        {
                            "suggest_method": channel.get("suggest_method", ""),
                            "no_sdk": channel.get("no_sdk", None),
                        }
                    ),
                    "is_public": channel["is_public"],
                    "is_confapi": channel.get("is_confapi", False),
                    # permission_level, verified_user_required 两个字段允许用户编辑，因此只会在创建时设置，更新时不会覆盖
                    "permission_level": PermissionLevelEnum(channel["permission_level"]).value,
                    "verified_user_required": channel["verified_user_required"],
                }

                try:
                    esb_channel = ESBChannel.objects.get(path=new_channel["path"], method=new_channel["method"])
                except ESBChannel.DoesNotExist:
                    channel_obj = self.create_channel_by_config(
                        new_channel,
                        default_update_fields,
                        force_update_fields,
                    )
                else:
                    remaining_official_channels.pop(esb_channel.id, None)
                    channel_obj = self.update_channel_by_config(
                        esb_channel,
                        new_channel,
                        default_update_fields,
                        force_update_fields,
                        allow_custom_config=bool(channel.get("config_fields")),
                    )

                if channel_obj and channel.get("config_fields"):
                    ESBChannelExtend.objects.update_or_create(
                        component=channel_obj,
                        defaults={
                            "config_fields": channel["config_fields"],
                        },
                    )

        if remaining_official_channels:
            self._hide_channels(remaining_official_channels.keys())

    def update_doc_category(self):
        conf_client = conf_tools.ConfClient()
        for system_doc_category in conf_client.system_doc_category:
            obj, _ = DocCategory.objects.get_or_create(
                name=system_doc_category["label"],
                defaults={
                    "priority": system_doc_category.get("priority", 1000),
                },
            )

            obj.name_en = system_doc_category.get("label_en")
            obj.data_type = DataTypeEnum.OFFICIAL_PUBLIC.value
            obj.save(update_fields=["data_type", "name_en"])

    def update_system_doc_category(self):
        # 获取 system 名称对应的 doc_category 名称
        conf_client = conf_tools.ConfClient()
        system_name_to_doc_category_name_map = {}
        for system_doc_category in conf_client.system_doc_category:
            for system_name in system_doc_category["systems"]:
                system_name_to_doc_category_name_map[system_name] = system_doc_category["label"]

        for system_config in conf_client.systems:
            system_name_to_doc_category_name_map[system_config.get("name")] = system_config.get("doc_category")

        system_name_to_obj_map = System.objects.get_name_to_obj_map()
        category_name_to_obj_map = DocCategory.objects.get_name_to_obj_map()
        for system_name, doc_category_name in system_name_to_doc_category_name_map.items():
            system = system_name_to_obj_map.get(system_name)
            doc_category = category_name_to_obj_map.get(doc_category_name)
            if not (system and doc_category):
                continue

            SystemDocCategory.objects.get_or_create(
                system=system,
                defaults={
                    "doc_category": doc_category,
                },
            )

    def get_by_fields(self, obj, fields):
        return {field: obj[field] for field in fields if field in obj}

    def diff_obj_conf(self, obj, conf, flag, default_update_fields, force_update_fields):
        info = []
        warning = []
        for fields, is_info_level in [(default_update_fields, True), (force_update_fields, self.force)]:
            for field in fields:
                if field not in conf:
                    continue

                if getattr(obj, field) != conf[field]:
                    msg = "%s: %s -> %s" % (field, getattr(obj, field), conf[field])
                    if is_info_level:
                        info.append(msg)
                    else:
                        warning.append(msg)

        if info:
            logger.info("%s changed: %s", flag, ", ".join(info))

        if warning:
            logger.warning("if force, %s will change: %s" % (flag, ", ".join(warning)))

    def _convert_system_legacy_fields_to_new(self, systems):
        new_systems = []
        for system in systems:
            new_system = {
                "name": system["name"],
                "description": system["label"],
                "description_en": system.get("label_en"),
                "comment": system["remark"],
                "comment_en": system.get("remark_en"),
                "is_public": system.get("is_public", True),
            }

            timeout = max(system.get("execute_timeout", 0), system.get("query_timeout", 0))
            if timeout:
                new_system["timeout"] = timeout

            new_systems.append(new_system)

        return new_systems

    def _convert_to_data_type(self, is_public: bool) -> int:
        if is_public:
            return DataTypeEnum.OFFICIAL_PUBLIC.value

        return DataTypeEnum.OFFICIAL_HIDDEN.value

    def _merge_dicts(self, *dicts):
        out = {}
        for d in dicts:
            if not d:
                continue
            out.update(d)
        return out

    def _get_official_channel_ids(self):
        official_system_ids = System.objects.get_official_ids()
        return list(ESBChannel.objects.filter(system_id__in=official_system_ids).values_list("id", flat=True))

    def _hide_channels(self, channel_ids):
        exclude_channels_config = settings.EXCLUDE_OFFICIAL_CHANNELS_WHEN_SYNCING
        try:
            # 环境变量只能传递字符串，需要先json格式化
            exclude_channels_config = json.loads(exclude_channels_config)
        except Exception:
            logger.warning("EXCLUDE_OFFICIAL_CHANNELS_WHEN_SYNCING is not a json format!")
            exclude_channels_config = []
        if exclude_channels_config:
            channel_ids_dict = dict.fromkeys(channel_ids, None)
            for channel in exclude_channels_config:
                if "board" in channel and "method" in channel and "path" in channel:
                    try:
                        exclude_channel_id = ESBChannel.objects.get(
                            board=channel["board"], method=channel["method"], path=channel["path"]
                        ).id
                        channel_ids_dict.pop(exclude_channel_id, None)
                    except ESBChannel.DoesNotExist:
                        logger.warning("channel does not exist: board=%s, method=%s, path=%s",
                            channel["board"], channel["method"], channel["path"])
                        continue
            channel_ids = channel_ids_dict.keys()
        ESBChannel.objects.filter(id__in=channel_ids).update(is_public=False)
