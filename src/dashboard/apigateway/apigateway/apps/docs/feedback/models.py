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
from django.db import models
from jsonfield import JSONField

from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin

from .constants import FeedbackDocTypeEnum, NoticeStatusEnum


class Feedback(TimestampedModelMixin, OperatorModelMixin):
    positive = models.BooleanField(default=False)
    doc_type = models.CharField("文档类型", choices=FeedbackDocTypeEnum.get_choices(), max_length=32)
    labels = JSONField("问题类型", default=list)
    link = models.CharField("文档链接", max_length=1024, default="", blank=True)
    content = models.TextField("反馈内容", default="", blank=True)
    screenshot = models.ImageField("截图", null=True, blank=True)

    def __str__(self):
        return f"<Feedback: {self.doc_type}/{self.id}>"

    class Meta:
        verbose_name = "文档反馈"
        verbose_name_plural = "文档反馈"
        db_table = "feedback"

    @property
    def screenshot_url(self):
        if not self.screenshot:
            return ""
        return self.screenshot.url


class FeedbackRelatedComponent(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE)
    board = models.CharField(max_length=64, blank=True, default="", db_index=True)
    system_name = models.CharField("组件系统", max_length=32)
    component_name = models.CharField("组件名称", max_length=64, blank=True, default="")

    def __str__(self):
        return f"<FeedbackRelatedComponent: {self.board}/{self.system_name}>"

    class Meta:
        verbose_name = "文档反馈-关联组件"
        verbose_name_plural = "文档反馈-关联组件"
        db_table = "feedback_related_component"


class FeedbackRelatedAPIGateway(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE)
    api_id = models.IntegerField(db_index=True)
    stage_name = models.CharField(max_length=64, default="", blank=True)
    resource_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"<FeedbackRelatedAPIGateway: {self.api_id}>"

    class Meta:
        verbose_name = "文档反馈-关联网关"
        verbose_name_plural = "文档反馈-关联网关"
        db_table = "feedback_related_apigateway"


class Notice(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE)
    receivers = models.CharField("接收人", max_length=1024)
    status = models.CharField("通知状态", max_length=32, choices=NoticeStatusEnum.get_choices())
    message = models.TextField("通知结果", default="", blank=True)

    def __str__(self):
        return f"<Notice: {self.id}>"

    class Meta:
        verbose_name = "文档反馈通知"
        verbose_name_plural = "文档反馈通知"
        db_table = "feedback_notice"
