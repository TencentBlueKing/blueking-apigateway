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
from typing import List

from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.apps.label.models import APILabel
from apigateway.apps.monitor.constants import (
    API_ALARM_TYPE_CHOICES,
    AlarmStatusEnum,
    AlarmTypeEnum,
    NoticeRoleEnum,
    ResourceBackendAlarmSubTypeEnum,
)
from apigateway.apps.monitor.managers import AlarmFilterConfigManager, AlarmRecordManager, AlarmStrategyManager
from apigateway.common.mixins.models import ConfigModelMixin
from apigateway.core.models import Gateway
from apigateway.schema.models import Schema

logger = logging.getLogger(__name__)


class AlarmFilterConfig(ConfigModelMixin):
    """
    告警过滤配置
    从请求记录中拉取告警事件后，可根据过滤配置，去除部分不需告警的记录
    """

    alarm_type = models.CharField(max_length=64, choices=AlarmTypeEnum.get_choices(), db_index=True)
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE, blank=True, null=True)
    schema = models.ForeignKey(Schema, on_delete=models.PROTECT)
    comment = models.CharField(max_length=512, blank=True, default="")

    objects = AlarmFilterConfigManager()

    def __str__(self):
        return f"<AlarmFilterConfig: {self.id}>"

    class Meta:
        verbose_name = _("监控告警过滤配置")
        verbose_name_plural = _("监控告警过滤配置")
        db_table = "monitor_alarm_filter_config"

    def save(self, *args, **kwargs):
        if self.alarm_type not in dict(AlarmTypeEnum.get_choices()):
            raise ValueError("type should be one of AlarmTypeEnum")

        # check the config value
        try:
            _ = self.config
        except Exception as e:
            logger.exception("the config field is not a valid json")
            raise e

        super().save(*args, **kwargs)


class AlarmStrategy(ConfigModelMixin):
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    alarm_type = models.CharField(max_length=64, choices=API_ALARM_TYPE_CHOICES, db_index=True)
    alarm_subtype = models.CharField(
        max_length=64,
        choices=ResourceBackendAlarmSubTypeEnum.get_choices(),
        db_index=True,
    )
    # TODO: 删除 _api_label_ids 字段
    _api_label_ids = models.TextField(db_column="api_label_ids", blank=True, default="")
    api_labels = models.ManyToManyField(APILabel)
    schema = models.ForeignKey(Schema, on_delete=models.PROTECT)
    enabled = models.BooleanField(default=True)

    objects = AlarmStrategyManager()

    def __str__(self):
        return f"<AlarmStrategy: {self.id}>"

    class Meta:
        verbose_name = _("监控告警策略")
        verbose_name_plural = _("监控告警策略")
        db_table = "monitor_alarm_strategy"

    @property
    def api_label_ids(self) -> List[int]:
        return list(self.api_labels.values_list("id", flat=True))

    @property
    def notice_receivers(self):
        receivers = set()

        config = self.config
        if NoticeRoleEnum.MAINTAINER.value in config["notice_config"]["notice_role"]:
            gateway = Gateway.objects.get(id=self.gateway_id)
            receivers.update(gateway.maintainers)
        if config["notice_config"]["notice_extra_receiver"]:
            receivers.update(config["notice_config"]["notice_extra_receiver"])
        return list(receivers)


class AlarmRecord(models.Model):
    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE, blank=True, null=True)
    alarm_strategies = models.ManyToManyField(AlarmStrategy)
    alarm_attr_id = models.IntegerField(_("监控平台告警特性ID"))
    alarm_id = models.CharField(_("监控平台告警ID"), max_length=32, db_index=True)
    source_time = models.DateTimeField(_("监控平台事件源时间"), null=True, blank=True)
    match_dimension = models.TextField(_("监控平台匹配维度"), default="", blank=True)
    status = models.CharField(_("告警状态"), max_length=32, choices=AlarmStatusEnum.get_choices())
    message = models.TextField(_("告警消息"), default="", blank=True)
    comment = models.TextField(default="", blank=True)
    created_time = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_time = models.DateTimeField(auto_now=True)

    objects = AlarmRecordManager()

    def __str__(self):
        return f"<AlarmRecord: {self.id}>"

    class Meta:
        verbose_name = _("监控告警记录")
        verbose_name_plural = _("监控告警记录")
        db_table = "monitor_alarm_record"
