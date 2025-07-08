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

import base64

from django import forms
from django.utils import timezone
from django.utils.encoding import force_text

from common.constants import API_TYPE_OP
from common.forms import BaseComponentForm, DefaultBooleanField, ListField, TypeCheckField
from components.component import Component, SetupConfMixin
from .toolkit import configs, tools


class SendWeixin(Component, SetupConfMixin):
    """
    apiLabel {{ _("发送微信消息") }}
    apiMethod POST

    ### {{ _("功能描述") }}

    {{ _("发送微信消息，支持微信公众号消息，及微信企业号消息") }}

    ### {{ _("请求参数") }}

    {{ common_args_desc }}

    #### {{ _("接口参数") }}

    | {{ _("字段") }}               |  {{ _("类型") }}      | {{ _("必选") }}   |  {{ _("描述") }}      |
    |--------------------|------------|--------|------------|
    | receiver           |  string    | {{ _("否") }}     | {{ _("微信接收者，包含绑定在指定公众号上的微信用户的 openid 或 企业号上的微信用户的用户ID，多个以逗号分隔") }} |
    | receiver__username |  string    | {{ _("否") }}     | {{ _("微信接收者，包含用户名，用户需在蓝鲸平台注册，多个以逗号分隔，若receiver、receiver__username同时存在，以receiver为准") }} |
    | data               |  dict      | {{ _("是") }}     | {{ _("消息内容") }} |
    | wx_qy_agentid      |  string    | {{ _("否") }}     | agentid of WeChat app |
    | wx_qy_corpsecret   |  string    | {{ _("否") }}     | secret of WeChat app |

    #### {{ _("data 参数包含内容") }}

    | {{ _("字段") }}               |  {{ _("类型") }}      | {{ _("必选") }}   |  {{ _("描述") }}      |
    |--------------------|------------|--------|------------|
    | heading            |  string    | {{ _("是") }}     | {{ _("通知头部文字") }} |
    | message            |  string    | {{ _("是") }}     | {{ _("通知文字") }} |
    | date               |  string    | {{ _("否") }}     | {{ _('通知发送时间，默认为当前时间 "YYYY-mm-dd HH:MM"') }} |
    | remark             |  string    | {{ _("否") }}     | {{ _("通知尾部文字") }} |
    | is_message_base64  |  bool      | {{ _("否") }}     | {{ _("通知文字message是否base64编码，默认False，不编码，若编码请使用base64.b64encode方法") }} |

    ### {{ _("请求参数示例") }}

    ```python
    {
        "bk_app_code": "esb_test",
        "bk_app_secret": "xxx",
        "bk_token": "xxx",
        "receiver": "xxx",
        "data": {
            "heading": "blueking alarm",
            "message": "This is a test.",
            "date": "2017-02-22 15:36",
            "remark": "This is a test!"
        }
    }
    ```

    ### {{ _("返回结果示例") }}

    ```python
    {
        "result": true,
        "code": "00",
        "message": "OK",
    }
    ```
    """  # noqa

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP
    contact_way = "wx_userid"

    class Form(BaseComponentForm):
        receiver = ListField(label="wechat receiver", required=False)
        receiver__username = ListField(label="wechat receiver", required=False)
        data = TypeCheckField(label="message data", promise_type=dict, required=True)

        def clean(self):
            data = self.cleaned_data

            if not (data["receiver"] or data["receiver__username"]):
                raise forms.ValidationError(
                    "WeChat receiver [receiver, receiver__username] shall not be empty at the same time"
                )
            if data["receiver"]:
                data["receiver__username"] = None

            return {
                "receiver": data["receiver"],
                "receiver__username": data["receiver__username"],
                "data": SendWeixin.DataForm(data["data"]).get_cleaned_data_or_error(),
            }

    class DataForm(BaseComponentForm):
        heading = forms.CharField(label="notification header text", required=True)
        message = forms.CharField(label="notification text", required=True)
        date = forms.CharField(label="notification sending time", required=False)
        remark = forms.CharField(label="notification tail text", required=False)
        is_message_base64 = DefaultBooleanField(
            label="notification text is encoded by base64 or not", default=False, required=False
        )

        def decode_message(self, message, is_message_base64):
            if is_message_base64:
                try:
                    message = force_text(base64.b64decode(message))
                except Exception:
                    pass
            return message

        def clean(self):
            data = self.cleaned_data
            data.update(
                {
                    "date": data.get("date"),
                    "message": self.decode_message(data["message"], data["is_message_base64"]),
                }
            )
            return data

    def get_mp_msg_data(self, data):
        return {
            "first": {"value": data["heading"]},
            "keyword1": {"value": data["message"]},
            "keyword2": {
                "value": data.get("date") or timezone.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            "remark": {"value": data.get("remark", "")},
        }

    def get_qy_msg_content(self, data):
        new_data = [
            data["heading"],
            force_text(data["message"]),
        ]

        if data.get("date"):
            new_data.append(u"Date: %s" % data["date"])

        if data.get("remark"):
            new_data.append(data["remark"])

        return "\n".join(new_data)

    def handle(self):
        # 微信类型，包括微信公众号"mp"，微信企业号"qy"
        self.wx_type = getattr(self, "wx_type", "") or getattr(configs, "wx_type", "")

        # 微信公众号配置
        # 组件会根据 wx_app_id & wx_secret 申请微信的 access_token，
        # 业务如希望集中管理 access_token，可优化 components/apis/weixin_mp/get_token.py 中 access_token 获取逻辑
        self.wx_app_id = getattr(self, "wx_app_id", "") or getattr(configs, "wx_app_id", "")
        self.wx_secret = getattr(self, "wx_secret", "") or getattr(configs, "wx_secret", "")
        self.wx_template_id = getattr(self, "wx_template_id", "") or getattr(configs, "wx_template_id", "")

        # 微信企业号配置
        # 支持蓝鲸应用传递企业微信应用账号信息 wx_qy_corpsecret + wx_qy_agentid ，以实现通过不同企业微信应用发送消息
        self.wx_qy_corpid = getattr(self, "wx_qy_corpid", "") or getattr(configs, "wx_qy_corpid", "")
        self.wx_qy_corpsecret = (
            self.request.kwargs.get("wx_qy_corpsecret")
            or getattr(self, "wx_qy_corpsecret", "")
            or getattr(configs, "wx_qy_corpsecret", "")
        )
        self.wx_qy_agentid = (
            self.request.kwargs.get("wx_qy_agentid")
            or getattr(self, "wx_qy_agentid", "")
            or getattr(configs, "wx_qy_agentid", "")
        )

        data = self.form_data
        # 根据蓝鲸平台用户数据，将用户名转换为微信用户ID
        if data["receiver__username"]:
            try:
                user_data = tools.get_receiver_with_username(
                    receiver__username=data["receiver__username"],
                    contact_way=self.contact_way,
                )
            except tools.NoValidUser as err:
                result = {
                    "result": False,
                    "message": force_text(err),
                }
                self.response.payload = tools.inject_invalid_usernames(result, err.invalid_usernames)
                return

            data.update(user_data)

        if self.wx_type == "mp":
            data.update(
                {
                    "appid": self.wx_app_id,
                    "secret": self.wx_secret,
                    "template_id": self.wx_template_id,
                    "url": self.request.kwargs.get("url", ""),
                    "touser": data["receiver"],
                    "data": self.get_mp_msg_data(data["data"]),
                }
            )
            result = self.invoke_other("generic.weixin_mp.send_msg_with_tpl", kwargs=data)
        elif self.wx_type in ["qy", "qywx"]:
            data.update(
                {
                    "corpid": self.wx_qy_corpid,
                    "corpsecret": self.wx_qy_corpsecret,
                    "agentid": self.wx_qy_agentid,
                    "touser": data["receiver"],
                    "content": self.get_qy_msg_content(data["data"]),
                }
            )
            result = self.invoke_other("generic.weixin_qy.send_message", kwargs=data)
        else:
            result = {"result": False, "message": "WeChat type that is not supported [wx_type=%s]" % self.wx_type}

        if result["result"] and data.get("_extra_user_error_msg"):
            result = {
                "result": False,
                "message": u"Some users failed to send wechat message. %s" % data["_extra_user_error_msg"],
            }
        self.response.payload = tools.inject_invalid_usernames(result, data.get("_invalid_usernames"))
