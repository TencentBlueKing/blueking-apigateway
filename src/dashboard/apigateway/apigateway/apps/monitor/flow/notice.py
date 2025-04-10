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
from abc import ABC, abstractmethod
from typing import List, Union

from django.conf import settings

from apigateway.apps.monitor.constants import NoticeWayEnum
from apigateway.components.cmsi import cmsi_component


class BaseNotice(ABC):
    @abstractmethod
    def send(self, sender: str, receivers: Union[str, List], message: str) -> List:
        """处理通知逻辑"""


class CMSIWechatNotice(BaseNotice):
    def send(self, tenant_id, sender, receivers, message):
        return cmsi_component.send_wechat(
            tenant_id,
            {
                "bk_username": sender,
                "receiver__username": receivers,
                "data": {
                    "message": message,
                },
            },
        )


class CMSIIMNotice(BaseNotice):
    def send(self, tenant_id, sender, receivers, message):
        params = {
            "bk_username": sender,
            "receiver__username": receivers,
            "title": "蓝鲸通知",
            "content": message,
        }
        return cmsi_component.send_im(tenant_id, params)


class CMSIMailNotice(BaseNotice):
    def send(self, tenant_id, sender, receivers, message):
        params = {
            "bk_username": sender,
            "receiver__username": receivers,
            "content": message,
            "title": "蓝鲸通知",
        }
        return cmsi_component.send_mail(tenant_id, params)


class NoticeWay:
    notice_way_map = {
        NoticeWayEnum.WECHAT.value: CMSIWechatNotice,
        NoticeWayEnum.IM.value: CMSIIMNotice,
        NoticeWayEnum.MAIL.value: CMSIMailNotice,
    }

    @classmethod
    def send_notice(cls, tenant_id, notice_way, sender, receivers, message):
        # TODO: 是否可删除 sender

        notice_class = cls.notice_way_map.get(notice_way)
        if not notice_class:
            return False, f"不支持指定的发送方式 {notice_way}"

        if getattr(settings, "FAKE_SEND_NOTICE", True):
            return False, "系统配置不实际发送消息"

        return notice_class().send(tenant_id, sender, receivers, message)
